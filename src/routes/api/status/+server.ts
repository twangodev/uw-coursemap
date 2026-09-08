import { json } from "@sveltejs/kit";
import { status } from "$lib/server/data";
export async function GET({ platform }) {
  return json(await status(platform), {
    headers: { "Cache-Control": "no-store" },
  });
}
