import { building } from "$app/environment";
import { redirect } from "@sveltejs/kit";
export function load({ url }) {
  redirect(308, "/departments" + (building ? "" : url.search));
}
