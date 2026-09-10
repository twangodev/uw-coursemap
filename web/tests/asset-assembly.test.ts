import { test, expect } from "vitest";
import {
  mkdtemp,
  mkdir,
  writeFile,
  readFile,
  access,
  rm,
} from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { assembleAssets } from "../assemble-assets.mjs";

test("assembles matching releases without publishing cache metadata; rejects mixed inputs", async () => {
  const root = await mkdtemp(join(tmpdir(), "uwcourses-assets-"));
  const site = join(root, "site");
  const output = join(root, "public");
  const release = JSON.stringify({
    revision: "revision",
    projection_id: "projection",
  });
  async function write(path: string, value: string) {
    const target = join(site, path);
    await mkdir(join(target, ".."), { recursive: true });
    await writeFile(target, value);
  }
  try {
    await mkdir(output);
    await write("import/status.json", release);
    await write("import/assets/data/evidence.json", "{}");
    for (const stage of ["documents", "social"]) {
      await write(`${stage}/.release.json`, release);
      await write(`${stage}/.cache-manifest.json`, "private");
    }
    await write("documents/__documents/page.json", "page");
    await write("documents/sitemap.xml", "sitemap");
    await write("social/social/card.png", "image");
    await assembleAssets(output, site);
    expect(await readFile(join(output, "data/evidence.json"), "utf8")).toBe(
      "{}",
    );
    expect(await readFile(join(output, "__documents/page.json"), "utf8")).toBe(
      "page",
    );
    expect(await readFile(join(output, "social/card.png"), "utf8")).toBe(
      "image",
    );
    expect(await readFile(join(output, "_headers"), "utf8")).toContain(
      "X-Robots-Tag: noindex",
    );
    await expect(
      access(join(output, ".cache-manifest.json")),
    ).rejects.toThrow();
    await expect(access(join(output, ".release.json"))).rejects.toThrow();
    await write(
      "documents/.release.json",
      JSON.stringify({ revision: "different", projection_id: "projection" }),
    );
    await expect(assembleAssets(output, site)).rejects.toThrow(
      "Mixed dataset inputs",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
