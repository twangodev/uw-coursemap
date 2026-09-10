import { expect, it, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: true }));
import { instructorSlug } from "../../src/lib/format";
import {
  instructorUrls,
  resolveInstructorUid,
} from "../../src/lib/server/instructor-urls";
import { query } from "../../src/lib/server/data";

it("matches original name sanitization, including transliteration", () => {
  expect(instructorSlug("Hobbes Legault")).toBe("HOBBES_LEGAULT");
  expect(instructorSlug(" O'Brien Jr. ")).toBe("OBRIEN_JR");
  expect(instructorSlug("José / Muñoz")).toBe("JOSE_MUNOZ");
});
it("keeps every instructor identity addressable without URL collisions", async () => {
  const urls = await instructorUrls();
  const rows = await query(undefined, "SELECT uid,name FROM instructors");
  expect(urls.size).toBe(rows.length);
  expect(new Set(urls.values()).size).toBe(rows.length);
  expect(urls.get("instructor_a65e64df990aa3bab98ee125")).toBe(
    "/instructors/HOBBES_LEGAULT",
  );
  const duplicates = rows.filter((row) => row.name === "Hobbes Legault");
  expect(duplicates.length).toBeGreaterThan(1);
  expect(new Set(duplicates.map((row) => urls.get(row.uid))).size).toBe(
    duplicates.length,
  );
});

it("resolves both current and historical profiles on demand", async () => {
  const release = await import("../../.site/import/entries.json");
  const urls = await instructorUrls();
  const selected = new Set(release.instructors);
  const historical = [...urls].find(([uid]) => !selected.has(uid))!;
  expect(await resolveInstructorUid(historical[1])).toBe(historical[0]);
});

it("publishes the same collision-safe URLs in bounded lookup shards", async () => {
  const { instructorUrlAsset } =
    await import("../../src/lib/server/instructor-urls");
  const { buildDocumentAsset, documentEntries } =
    await import("../../src/lib/server/documents/build");
  const entries = await documentEntries();
  const paths = entries.filter(({ path }) =>
    path.startsWith("instructor-urls/"),
  );
  expect(paths.length).toBeLessThanOrEqual(256);
  const shards = new Map(
    await Promise.all(
      paths.map(
        async ({ path }) => [path, await buildDocumentAsset(path)] as const,
      ),
    ),
  );
  for (const [uid, url] of await instructorUrls()) {
    const path = instructorUrlAsset(uid).slice("/__documents/".length);
    expect(shards.get(path)[uid]).toBe(url);
  }
  expect(await buildDocumentAsset("search-metadata.json")).toHaveProperty(
    "mean",
  );
});
