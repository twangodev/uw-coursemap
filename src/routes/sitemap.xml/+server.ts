import { sitemapPages, sitemapXml, xmlHeaders } from "$lib/server/sitemap";
export const prerender = true;
export async function GET() {
  return new Response(
    sitemapXml(
      [...(await sitemapPages()).keys()].map((page) => `/sitemaps/${page}`),
      true,
    ),
    { headers: xmlHeaders },
  );
}
