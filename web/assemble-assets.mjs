import { cp, readdir, appendFile, readFile } from "node:fs/promises";

/** Only completed stage outputs are copied; cache metadata never becomes public. */
export async function assembleAssets(
  output = ".svelte-kit/cloudflare",
  site = ".site",
) {
  const imported = JSON.parse(
    await readFile(`${site}/import/status.json`, "utf8"),
  );
  for (const stage of ["documents", "social"]) {
    const release = JSON.parse(
      await readFile(`${site}/${stage}/.release.json`, "utf8"),
    );
    if (
      release.revision !== imported.revision ||
      release.projection_id !== imported.projection_id
    )
      throw new Error(`Mixed dataset inputs: rebuild ${stage}`);
  }
  for (const source of [
    `${site}/import/assets`,
    `${site}/documents`,
    `${site}/social`,
  ]) {
    for (const entry of await readdir(source, { withFileTypes: true })) {
      if (entry.name.startsWith(".")) continue;
      await cp(`${source}/${entry.name}`, `${output}/${entry.name}`, {
        recursive: true,
      });
    }
  }
  await appendFile(
    `${output}/_headers`,
    "\n/__documents/*\n  X-Robots-Tag: noindex\n/social/manifest.json\n  X-Robots-Tag: noindex\n",
  );
}
