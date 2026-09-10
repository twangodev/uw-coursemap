/** Build-time social cards; the dev middleware uses the same renderer on demand. */
import { chromium } from "playwright";
import { readFile, writeFile, mkdir, rename } from "node:fs/promises";
import { resolve, dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import { createHash, randomUUID } from "node:crypto";

const prefix = "/social/pages/";
/** @param {string} html */
export function cardFromHtml(html) {
  const image = html.match(/property="og:image" content="([^"]+)"/)?.[1];
  if (!image) return null;
  const path = new URL(image).pathname;
  if (!path.startsWith(prefix)) return null;
  /** @type {Record<string, any>[]} */
  const graph =
    JSON.parse(
      html.match(
        /<script type="application\/ld\+json">(.*?)<\/script>/s,
      )?.[1] || "{}",
    )["@graph"] || [];
  const page = graph.find((item) =>
    ["WebPage", "CollectionPage"].includes(item["@type"]),
  );
  if (!page) return null;
  const course = graph.find((item) => item["@type"] === "Course");
  const person = graph.find((item) => item["@type"] === "Person");
  const department = graph
    .find((item) => item["@type"] === "BreadcrumbList")
    ?.itemListElement?.find(
      (/** @type {{item: string, name: string}} */ item) =>
        /\/departments\/[^/]+$/.test(item.item),
    )?.name;
  const pageTitle = page.name
    .replace(/\s*\|.*$/, "")
    .replace(/ Prerequisite Map$/i, "");
  return {
    path,
    label:
      course?.courseCode ||
      (person
        ? "Professor"
        : path.endsWith("/easiest.png")
          ? "Easiest courses"
          : path.endsWith("/hardest.png")
            ? "Hardest courses"
            : path.endsWith("/catalog.png")
              ? "Course catalog"
              : path.includes("/courses/")
                ? "Course"
                : path.includes("/explorer/")
                  ? "Prerequisite map"
                  : "Department"),
    title: course?.name || person?.name || department || pageTitle,
  };
}

export async function createCardRenderer() {
  const sources = await Promise.all(
    [
      "web/social-card.html",
      "static/fonts/OverusedGrotesk-VF.woff2",
      "static/uwcourses-logo.svg",
    ].map((path) => readFile(path)),
  );
  const version = createHash("sha256")
    .update(Buffer.concat(sources))
    .digest("hex");
  const browser = await chromium.launch();
  const cache = resolve(".site/social-cache");
  await mkdir(cache, { recursive: true });
  return {
    async worker() {
      const page = await browser.newPage({
        viewport: { width: 1200, height: 630 },
        deviceScaleFactor: 1,
      });
      await page.goto(pathToFileURL(resolve("web/social-card.html")).href);
      await page.evaluate(() => document.fonts.ready);
      /** @param {{ title: string, label: string }} card */
      return async ({ title, label }) => {
        const key = createHash("sha256")
          .update(JSON.stringify([version, title, label]))
          .digest("hex");
        const file = join(cache, key + ".png");
        try {
          return await readFile(file);
        } catch (error) {
          if (
            !(error instanceof Error) ||
            !("code" in error) ||
            error.code !== "ENOENT"
          )
            throw error;
        }
        await page.evaluate(
          ({ title, label }) => {
            const labelNode = document.querySelector(".label");
            const heading = document.querySelector("h1");
            if (!labelNode || !heading)
              throw new Error("Social card template is incomplete");
            labelNode.textContent = label;
            heading.textContent = title;
            let size = 80;
            heading.style.fontSize = size + "px";
            while (heading.getBoundingClientRect().height > 260 && size > 36)
              heading.style.fontSize = --size + "px";
            if (heading.getBoundingClientRect().height > 260)
              throw new Error("Social card title does not fit: " + title);
          },
          { title, label },
        );
        const png = await page.screenshot();
        const temporary = file + "." + randomUUID();
        await writeFile(temporary, png);
        await rename(temporary, file);
        return png;
      };
    },
    close: () => browser.close(),
  };
}

export async function buildSocialImages(output = ".svelte-kit/cloudflare") {
  const manifest = JSON.parse(
    await readFile(join(output, "social/manifest.json"), "utf8"),
  );
  const cards = new Map(
    manifest.map((/** @type {{path: string}} */ card) => [card.path, card]),
  );
  const renderer = await createCardRenderer();
  const pending = [...cards.values()];
  let completed = 0;
  try {
    await Promise.all(
      Array.from({ length: 6 }, async () => {
        const render = await renderer.worker();
        for (let card; (card = pending.pop()); ) {
          const png = await render(card);
          const file = resolve(output, "." + decodeURIComponent(card.path));
          if (!file.startsWith(resolve(output) + "/"))
            throw new Error("Invalid social image path");
          await mkdir(dirname(file), { recursive: true });
          await writeFile(file, png);
          if (++completed % 2000 === 0)
            console.log(`Social cards: ${completed}/${cards.size}`);
        }
      }),
    );
  } finally {
    await renderer.close();
  }
  console.log(`Generated ${cards.size} page-specific social cards.`);
}

/** @returns {import("vite").Plugin} */
export function socialImagesDev() {
  return {
    name: "social-images-dev",
    enforce: "pre",
    configureServer(server) {
      /** @type {ReturnType<typeof createCardRenderer> | undefined} */
      let renderer;
      /** @type {Promise<(card: {title: string, label: string}) => Promise<Buffer>> | undefined} */
      let worker;
      let queue = Promise.resolve();
      server.httpServer?.once("close", () => {
        renderer?.then((r) => r.close());
      });
      server.middlewares.use((req, res, next) => {
        const path = new URL(req.url || "/", "http://localhost").pathname;
        if (!path.startsWith(prefix)) return next();
        queue = queue
          .then(async () => {
            if (
              !/^\/social\/pages\/(courses|instructors|departments|explorer)\/.+\.png$/.test(
                path,
              )
            ) {
              res.statusCode = 404;
              res.end();
              return;
            }
            const address = server.httpServer?.address();
            if (!address || typeof address === "string")
              throw new Error("Dev server has no TCP address");
            const source = path.slice("/social/pages".length, -4);
            const response = await fetch(
              `http://127.0.0.1:${address.port}${source}`,
            );
            const card = response.ok
              ? cardFromHtml(await response.text())
              : null;
            if (!card || card.path !== path) {
              res.statusCode = 404;
              res.end();
              return;
            }
            renderer ??= createCardRenderer();
            worker ??= renderer.then((r) => r.worker());
            const png = await (await worker)(card);
            res.setHeader("Content-Type", "image/png");
            res.end(png);
          })
          .catch((error) => {
            server.config.logger.error(String(error));
            res.statusCode = 500;
            res.end();
          });
      });
    },
  };
}
