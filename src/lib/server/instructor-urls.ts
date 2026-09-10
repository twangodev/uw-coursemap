import { instructorSlug } from "$lib/format";
import { query, status } from "./data";
import { building, dev } from "$lib/server/runtime";
import { error } from "@sveltejs/kit";
import { instructorBucket, readAsset } from "./documents/storage";

export function instructorUrlAsset(uid: string) {
  return `/__documents/instructor-urls/${instructorBucket(uid).slice(0, 2)}.json`;
}

let cached:
  | { revision: string; index: Promise<Map<string, string>> }
  | undefined;

/** Preserve name URLs while keeping distinct dataset identities addressable. */
export async function instructorUrls(platform?: App.Platform) {
  const { revision } = await status(platform);
  if (!cached || cached.revision !== revision) {
    const index = query(
      platform,
      "SELECT uid,name FROM instructors ORDER BY current DESC,COALESCE(json_extract(payload,'$.ratings.quality_count'),0) DESC,uid",
    ).then((rows) => {
      const urls = new Map<string, string>();
      const used = new Set<string>();
      for (const row of rows) {
        const name = instructorSlug(row.name || "Unknown instructor");
        // The old name URL prefers a current, reviewed record. Other identities
        // retain their own page; no grades or reviews are combined by name.
        const slug = used.has(name) ? `${name}--${row.uid}` : name;
        used.add(slug);
        urls.set(row.uid, "/instructors/" + encodeURIComponent(slug));
      }
      return urls;
    });
    cached = { revision, index };
    index.catch(() => {
      if (cached?.index === index) cached = undefined;
    });
  }
  return cached.index;
}

export async function withInstructorUrls<
  T extends { uid?: string; instructor_uid?: string },
>(rows: T[], platform?: App.Platform) {
  if (!rows.length) return [];
  if (!building && !dev) {
    const assets = await Promise.all(
      [
        ...new Set(
          rows.map((row) =>
            instructorUrlAsset(row.instructor_uid || row.uid || ""),
          ),
        ),
      ].map(async (path) => {
        const urls = await readAsset<Record<string, string>>(path, platform);
        if (!urls) error(503, "Published instructor URLs unavailable");
        return urls;
      }),
    );
    const urls = Object.assign({}, ...assets) as Record<string, string>;
    return rows.map((row) => {
      const url = urls[row.instructor_uid || row.uid || ""];
      if (!url) error(503, "Published instructor URL unavailable");
      return { ...row, instructor_url: url };
    });
  }
  const urls = await instructorUrls(platform);
  return rows.map((row) => ({
    ...row,
    instructor_url: urls.get(row.instructor_uid || row.uid || ""),
  }));
}

// Reverse lookup is cached with the revision's URL map, including on the Worker.
const reverseIndexes = new WeakMap<Map<string, string>, Map<string, string>>();
export async function resolveInstructorUid(
  path: string,
  platform?: App.Platform,
) {
  const urls = await instructorUrls(platform);
  let reverse = reverseIndexes.get(urls);
  if (!reverse) {
    reverse = new Map([...urls].map(([uid, url]) => [url, uid]));
    reverseIndexes.set(urls, reverse);
  }
  return reverse.get(path);
}
