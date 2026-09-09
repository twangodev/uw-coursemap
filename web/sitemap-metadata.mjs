/** Finalize sitemap metadata against the actual prerendered page content. */
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve, dirname, join } from "node:path";
import { createHash } from "node:crypto";

/** @param {string} value */
const hash = (value) => createHash("sha256").update(value).digest("hex");
/** @param {string} value */
const unescapeXml = (value) =>
  value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
/** @param {string} html */
export function pageFingerprint(html) {
  const main =
    html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/)?.[1] ||
    html.split("<body")[1] ||
    html;
  const content = main
    .replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/g, "")
    .replace(/<!--[\s\S]*?-->/g, "");
  const metadata = [
    ...html.matchAll(
      /<title>.*?<\/title>|<meta\s+name="description"[^>]*>|<script type="application\/ld\+json">.*?<\/script>/gs,
    ),
  ]
    .map((match) => match[0])
    .join("");
  return hash(content + metadata);
}
/** @param {string} path */
export function sitemapPolicy(path) {
  if (path === "/") return { priority: "1.0", changefreq: "weekly" };
  if (path === "/departments" || path.startsWith("/courses/"))
    return { priority: "0.8", changefreq: "monthly" };
  if (path.startsWith("/departments/"))
    return { priority: "0.7", changefreq: "monthly" };
  if (path.startsWith("/instructors/"))
    return { priority: "0.6", changefreq: "monthly" };
  return { priority: "0.5", changefreq: "monthly" };
}

/** @typedef {{ hash: string, lastmod: string }} Stamp */
/** @param {string} fingerprint @param {Stamp | undefined} previous @param {string} now @returns {Stamp} */
export function revisionStamp(fingerprint, previous, now) {
  return previous?.hash === fingerprint &&
    Number.isFinite(Date.parse(previous.lastmod))
    ? previous
    : { hash: fingerprint, lastmod: now };
}

export async function finalizeSitemaps({
  pages = ".svelte-kit/output/prerendered/pages",
  output = ".svelte-kit/cloudflare",
  history = ".site/sitemap-history.json",
  now = new Date().toISOString(),
} = {}) {
  /** @type {Record<string, Stamp>} */
  let previous = {};
  try {
    previous = JSON.parse(await readFile(history, "utf8"));
  } catch (error) {
    if (
      !(error instanceof Error) ||
      !("code" in error) ||
      error.code !== "ENOENT"
    )
      throw error;
  }
  /** @type {Record<string, Stamp>} */
  const next = {};
  const index = await readFile(join(pages, "sitemap.xml"), "utf8");
  /** @type {Map<string, string>} */
  const sitemapDates = new Map();
  for (const match of index.matchAll(/<loc>(.*?)<\/loc>/g)) {
    const url = unescapeXml(match[1]);
    const relative = new URL(url).pathname.slice(1);
    const xml = await readFile(join(pages, relative), "utf8");
    const items = [];
    for (const entry of xml.matchAll(/<url>([\s\S]*?)<\/url>/g)) {
      const loc = entry[1].match(/<loc>(.*?)<\/loc>/)?.[1];
      if (!loc) throw new Error("Sitemap entry has no location");
      const pageUrl = unescapeXml(loc);
      const path = decodeURIComponent(new URL(pageUrl).pathname);
      const file = path === "/" ? "index.html" : path.slice(1) + ".html";
      const html = await readFile(join(pages, file), "utf8");
      const stamp = revisionStamp(
        pageFingerprint(html),
        previous[pageUrl],
        now,
      );
      next[pageUrl] = stamp;
      const { priority, changefreq } = sitemapPolicy(path);
      items.push(
        `<url><loc>${loc}</loc><lastmod>${stamp.lastmod}</lastmod><changefreq>${changefreq}</changefreq><priority>${priority}</priority></url>`,
      );
    }
    const result = xml.replace(
      /<urlset([^>]*)>[\s\S]*<\/urlset>/,
      `<urlset$1>${items.join("")}</urlset>`,
    );
    next[url] = revisionStamp(hash(result), previous[url], now);
    sitemapDates.set(match[1], next[url].lastmod);
    for (const root of new Set([pages, output]))
      await writeFile(join(root, relative), result);
  }
  const result = index.replace(
    /<sitemap>([\s\S]*?)<\/sitemap>/g,
    (_, entry) => {
      const loc = entry.match(/<loc>(.*?)<\/loc>/)?.[1];
      return `<sitemap><loc>${loc}</loc><lastmod>${sitemapDates.get(loc)}</lastmod></sitemap>`;
    },
  );
  for (const root of new Set([pages, output]))
    await writeFile(join(root, "sitemap.xml"), result);
  await mkdir(dirname(history), { recursive: true });
  await writeFile(history, JSON.stringify(next));
  console.log(
    `Finalized sitemap dates and priorities for ${Object.keys(next).length - sitemapDates.size} pages.`,
  );
}

/** @returns {import('vite').Plugin} */
export function sitemapMetadataDev() {
  return {
    name: "built-sitemap-metadata",
    enforce: "pre",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const path = new URL(req.url || "/", "http://localhost").pathname;
        if (
          !/^\/(sitemap\.xml|sitemaps\/(pages|courses|instructors)-\d+\.xml)$/.test(
            path,
          )
        )
          return next();
        try {
          const xml = await readFile(
            resolve(".svelte-kit/cloudflare", "." + path),
            "utf8",
          );
          if (!xml.includes("<lastmod>")) return next();
          res.setHeader("Content-Type", "application/xml; charset=utf-8");
          res.end(xml);
        } catch (error) {
          if (
            error instanceof Error &&
            "code" in error &&
            error.code === "ENOENT"
          )
            return next();
          next(error);
        }
      });
    },
  };
}
