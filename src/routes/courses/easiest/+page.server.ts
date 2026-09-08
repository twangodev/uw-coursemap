import { redirect } from "@sveltejs/kit";
export function load() {
  redirect(308, "/search?sort=gpa");
}
