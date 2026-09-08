import { status } from "$lib/server/data";
export async function load({ platform }) {
  return { status: await status(platform) };
}
