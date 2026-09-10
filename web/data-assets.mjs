import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { resolve, extname } from "node:path";

/** Serve prepared data in development, using the same paths as Worker assets.
 * @returns {import("vite").Plugin}
 */
export function dataAssetsDev() {
  return {
    name: "prepared-data-assets",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!["GET", "HEAD"].includes(req.method || "GET")) return next();
        let path;
        try {
          path = decodeURIComponent(
            new URL(req.url || "/", "http://localhost").pathname,
          );
        } catch {
          return next();
        }
        const root = path.startsWith("/data/")
          ? ".site/import/assets"
          : path.startsWith("/__documents/") ||
              path === "/sitemap.xml" ||
              path.startsWith("/sitemaps/") ||
              path === "/social/manifest.json"
            ? ".site/documents"
            : null;
        if (!root || path.split("/").some((part) => part.startsWith(".")))
          return next();
        const target = resolve(root, "." + path);
        if (!target.startsWith(resolve(root) + "/")) return next();
        try {
          if (!(await stat(target)).isFile()) return next();
          res.setHeader(
            "Content-Type",
            extname(target) === ".xml" ? "application/xml" : "application/json",
          );
          if (
            path.startsWith("/__documents/") ||
            path === "/social/manifest.json"
          )
            res.setHeader("X-Robots-Tag", "noindex");
          if (req.method === "HEAD") return res.end();
          createReadStream(target).on("error", next).pipe(res);
        } catch {
          next();
        }
      });
    },
  };
}
