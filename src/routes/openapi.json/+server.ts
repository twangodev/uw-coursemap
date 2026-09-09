import { json } from "@sveltejs/kit";
import { openapiSpec } from "$lib/api/openapi";
export const prerender = true;
export const GET = () =>
  json(openapiSpec(), {
    headers: { "Access-Control-Allow-Origin": "*", "X-Robots-Tag": "noindex" },
  });
