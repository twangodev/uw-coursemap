import { DatabaseSync } from "node:sqlite";
import { randomUUID } from "node:crypto";
import { getPlatformProxy } from "wrangler";

/** Copy the full dataset into an isolated local D1, using bounded API batches. */
export default async function setup() {
  const source = new DatabaseSync(".site/import/site.sqlite", { readOnly: true });
  const platform = await getPlatformProxy<{ DB: D1Database }>({
    remoteBindings: false,
    persist: { path: ".site/browser-state/v3" },
  });
  const db = platform.env.DB;
  const tables = source
    .prepare(
      "SELECT name,sql FROM sqlite_master WHERE type='table' AND (name NOT LIKE 'search%' OR name='search') AND name NOT LIKE 'sqlite_%'",
    )
    .all() as { name: string; sql: string }[];
  const identifier = (name: string) => '"' + name.replaceAll('"', '""') + '"';
  try {
    for (const { name, sql } of tables) {
      console.log(`Seeding browser D1: ${name}`);
      await db.prepare(`DROP TABLE IF EXISTS ${identifier(name)}`).run();
      await db.prepare(sql).run();
      const statement = source.prepare(`SELECT * FROM ${identifier(name)}`);
      statement.setReturnArrays(true);
      let rows: (string | number | null)[][] = [];
      let batch: D1PreparedStatement[] = [];
      const flushBatch = async () => {
        if (!batch.length) return;
        await db.batch(batch);
        batch = [];
      };
      const flush = async () => {
        if (!rows.length) return;
        batch.push(
          db
            .prepare(
              `INSERT INTO ${identifier(name)} VALUES ${rows.map((row) => `(${row.map(() => "?").join(",")})`).join(",")}`,
            )
            .bind(...rows.flat()),
        );
        rows = [];
        // Amortize local Worker round trips while keeping memory bounded.
        if (batch.length >= 100) await flushBatch();
      };
      for (const row of statement.iterate()) {
        const values = row as unknown as (string | number | null)[];
        // D1 permits at most 100 bound parameters per statement.
        if ((rows.length + 1) * values.length > 100) await flush();
        rows.push(values);
      }
      await flush();
      await flushBatch();
    }
    for (const { sql } of source
      .prepare(
        "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'search%'",
      )
      .all())
      await db.prepare(String(sql)).run();
    await db.batch([
      db.prepare("INSERT OR REPLACE INTO metadata VALUES ('ready', 'true')"),
      db
        .prepare("INSERT OR REPLACE INTO metadata VALUES ('serving', ?)")
        .bind(randomUUID().replaceAll("-", "")),
    ]);
  } finally {
    source.close();
    await platform.dispose();
  }
}
