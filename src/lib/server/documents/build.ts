import { building } from "$lib/server/runtime";
import { error } from "@sveltejs/kit";
import { query, status } from "$lib/server/data";
import {
  instructorUrls,
  instructorUrlAsset,
} from "$lib/server/instructor-urls";
import { instructorRatingPrior } from "$lib/server/instructor-ratings";
import { courseContext } from "$lib/server/course-context";
import { courseUrl } from "$lib/format";
import { documentKind, documentSchemas } from "$lib/api/schemas";
import { pageSeo } from "$lib/seo";
import { loadSourceDocument } from "./index";
import { documentAsset } from "./storage";
import entries from "../../../../.site/import/entries.json";

let inventory: ReturnType<typeof createInventory> | undefined;
async function createInventory() {
  const [courses, instructors, aliases] = await Promise.all([
    query(undefined, "SELECT uid,code FROM courses ORDER BY code"),
    instructorUrls(),
    query(
      undefined,
      "SELECT a.alias,c.code FROM aliases a JOIN courses c ON c.uid=a.uid ORDER BY a.alias,c.code",
    ),
  ]);
  const paths = [
    "/",
    "/search",
    "/stats",
    "/departments",
    "/explorer",
    "/explorer/all",
    "/instructors/by-rating-count",
    "/courses/easiest",
    "/courses/hardest",
    ...courses.map((c) => courseUrl(c.code)),
    ...instructors.values(),
    ...entries.subjects.flatMap((subject) =>
      ["", "/catalog", "/easiest", "/hardest"]
        .map((tail) => `/departments/${encodeURIComponent(subject)}${tail}`)
        .concat(`/explorer/${encodeURIComponent(subject)}`),
    ),
  ];
  const assets = new Map<string, string[]>();
  for (const path of new Set(paths)) {
    const asset = decodeURIComponent(
      documentAsset(path).slice("/__documents/".length),
    );
    const group = assets.get(asset) || [];
    group.push(path);
    assets.set(asset, group);
  }
  const courseAliases: Record<string, string> = {};
  const instructorUrlShards = new Map<string, Record<string, string>>();
  for (const [uid, url] of instructors) {
    const path = instructorUrlAsset(uid).slice("/__documents/".length);
    const shard = instructorUrlShards.get(path) || {};
    shard[uid] = url;
    instructorUrlShards.set(path, shard);
  }
  for (const row of aliases) {
    const target = courseUrl(row.code);
    courseAliases[row.alias] =
      courseAliases[row.alias] && courseAliases[row.alias] !== target
        ? "/search?q=" + encodeURIComponent(row.alias)
        : target;
  }
  return {
    assets,
    courses,
    instructorUrlShards,
    redirects: {
      courses: courseAliases,
      instructors: Object.fromEntries(instructors),
      subjects: entries.subjects,
    },
  };
}
function getInventory() {
  if (!building) error(404, "Build endpoint");
  return (inventory ??= createInventory());
}
export async function documentEntries() {
  const { assets, courses, instructorUrlShards } = await getInventory();
  return [
    ...assets.keys(),
    "redirects.json",
    "search-metadata.json",
    ...instructorUrlShards.keys(),
    ...courses.map((c) => `contexts/${c.uid}.json`),
  ].map((path) => ({ path }));
}
export async function generateDocument(path: string) {
  const url = new URL(path, "https://uwcourses.com");
  const data = await loadSourceDocument({
    url,
    params: {},
    setHeaders: () => {},
  });
  const dataset = await status();
  const document = {
    schema_version: 1,
    url: url.href,
    title: pageSeo({ ...data, status: dataset }, path).title,
    dataset,
    data,
  };
  // Validate without stripping SSR-only fields; the public API serves these same bytes.
  const serialized = JSON.parse(JSON.stringify(document));
  documentSchemas[documentKind(path)].parse(serialized);
  return serialized;
}
export async function buildDocumentAsset(asset: string) {
  const { assets, redirects, instructorUrlShards } = await getInventory();
  if (asset === "search-metadata.json")
    return { mean: await instructorRatingPrior() };
  if (instructorUrlShards.has(asset)) return instructorUrlShards.get(asset);
  if (asset === "redirects.json") return redirects;
  if (asset.startsWith("contexts/") && asset.endsWith(".json")) {
    const uid = asset.slice("contexts/".length, -5);
    const [row] = await query(
      undefined,
      "SELECT payload FROM courses WHERE uid=?",
      [uid],
    );
    if (!row) error(404, "Course not found");
    return { context: await courseContext(JSON.parse(row.payload)) };
  }
  const paths = assets.get(asset);
  if (!paths) error(404, "Document not found");
  if (!asset.startsWith("instructors/")) return generateDocument(paths[0]);
  const documents: Record<string, unknown> = {};
  for (const path of paths) documents[path] = await generateDocument(path);
  return documents;
}
