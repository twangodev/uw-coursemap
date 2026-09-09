import { documentSchemas, documentKind } from "$lib/api/schemas";
import { isRedirect } from "@sveltejs/kit";
import { loadDocument } from "./index";
import { documentMarkdown } from "./markdown";
import { pageSeo } from "$lib/seo";
import { representationUrl, type representation } from "$lib/documents";
import { status } from "$lib/server/data";
import type { RequestEvent } from "@sveltejs/kit";

export async function documentResponse(
  event: RequestEvent,
  requested: NonNullable<ReturnType<typeof representation>>,
) {
  if (event.request.method === "OPTIONS")
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "If-None-Match",
        "Access-Control-Max-Age": "86400",
      },
    });
  if (!["GET", "HEAD"].includes(event.request.method))
    return new Response(null, {
      status: 405,
      headers: { Allow: "GET, HEAD, OPTIONS" },
    });
  const url = new URL(event.url);
  url.pathname = requested.path;
  try {
    const [data, dataset] = await Promise.all([
      loadDocument({
        url,
        platform: event.platform,
        params: {},
        setHeaders: () => {},
      }),
      status(event.platform),
    ]);
    const seo = pageSeo({ ...data, status: dataset }, url.pathname);
    const canonical = new URL(
      url.pathname + url.search,
      "https://uwcourses.com",
    ).href;
    const document = documentSchemas[documentKind(url.pathname)].parse(
      JSON.parse(
        JSON.stringify({
          schema_version: 1,
          url: canonical,
          title: seo.title,
          dataset,
          data,
        }),
      ),
    );
    const body =
      requested.format === "json"
        ? JSON.stringify(document)
        : documentMarkdown(document);
    return new Response(event.request.method === "HEAD" ? null : body, {
      headers: {
        "Content-Type":
          requested.format === "json"
            ? "application/json; charset=utf-8"
            : "text/markdown; charset=utf-8",
        "X-Robots-Tag": "noindex",
        Link: `<${canonical}>; rel="canonical"`,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": "ETag, Link, X-Cache",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (cause) {
    if (isRedirect(cause)) {
      const target = new URL(cause.location, url);
      return new Response(null, {
        status: cause.status,
        headers: {
          Location: representationUrl(
            target.pathname,
            requested.format,
            target.search,
          ),
        },
      });
    }
    throw cause;
  }
}
