import { json } from "@sveltejs/kit";
import {
  documentEntries,
  buildDocumentAsset,
} from "$lib/server/documents/build";
export const prerender = true;
export const entries = documentEntries;
export async function GET({ params }) {
  return json(await buildDocumentAsset(params.path), {
    headers: {
      "X-Robots-Tag": "noindex",
      "Cache-Control": "public, max-age=0, must-revalidate",
    },
  });
}
