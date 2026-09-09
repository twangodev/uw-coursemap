import { error } from "@sveltejs/kit";
import { sitemapPages, sitemapXml, xmlHeaders } from "$lib/server/sitemap";
export const prerender = true;
export async function entries() {
  return [...(await sitemapPages()).keys()].map((page) => ({ page }));
}
export async function GET({ params }) {
  const paths = (await sitemapPages()).get(params.page);
  if (!paths) error(404, "Sitemap not found");
  return new Response(sitemapXml(paths), { headers: xmlHeaders });
}
