import { execFileSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { randomUUID } from "node:crypto";

/** Seed the production Worker's isolated local D1 before browser tests run. */
export default function setup() {
  const parts = readdirSync(".site/sql")
    .filter((file) => file.endsWith(".sql"))
    .sort();
  if (!parts.length)
    throw new Error("Run the dataset import before browser tests");
  const execute = (...args: string[]) =>
    execFileSync(
      "bun",
      [
        "x",
        "--no-install",
        "wrangler",
        "d1",
        "execute",
        "DB",
        "--local",
        "--persist-to",
        ".site/browser-state",
        ...args,
      ],
      { stdio: ["ignore", "ignore", "inherit"] },
    );
  for (const part of parts) {
    console.log(`Seeding browser D1: ${part}`);
    execute("--file", `.site/sql/${part}`);
  }
  execute(
    "--command",
    `INSERT OR REPLACE INTO metadata VALUES ('serving', '${randomUUID().replaceAll("-", "")}')`,
  );
}
