import { building } from "$app/environment";
import { redirect } from "@sveltejs/kit";
export function load({ params, url }) {
  redirect(
    308,
    `/departments/${encodeURIComponent(params.subject.toUpperCase())}` +
      (building ? "" : url.search),
  );
}
