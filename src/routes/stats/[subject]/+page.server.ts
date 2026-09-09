import { building } from "$app/environment";
import { redirect } from "@sveltejs/kit";
export { entries, prerender } from "../../departments/[subject]/+page.server";
export function load({ params, url }) {
  redirect(
    308,
    `/departments/${encodeURIComponent(params.subject.toUpperCase())}` +
      (building ? "" : url.search),
  );
}
