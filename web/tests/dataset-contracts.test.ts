import { expect, it } from "vitest";
import { DatabaseSync } from "node:sqlite";
import { courseSchema, instructorSchema } from "../../src/lib/api/schemas";
it("accepts every imported course and instructor in the pinned dataset", () => {
  const db = new DatabaseSync(".site/site.sqlite", { readOnly: true });
  const errors: string[] = [];
  try {
    for (const [table, schema] of [
      ["courses", courseSchema],
      ["instructors", instructorSchema],
    ] as const) {
      for (const row of db
        .prepare(`SELECT uid,payload FROM ${table}`)
        .iterate()) {
        const result = schema.safeParse(JSON.parse(String(row.payload)));
        if (!result.success && errors.length < 20)
          errors.push(
            `${row.uid}: ${result.error.issues.map((issue) => `${issue.path.join(".")}: ${issue.message}`).join("; ")}`,
          );
      }
    }
    expect(errors).toEqual([]);
  } finally {
    db.close();
  }
}, 60_000);
