import type { NavItem } from "$lib/types/nav.ts";
import { m } from "$lib/paraglide/messages";
import { localizeHref } from "$lib/paraglide/runtime";

export const navigation: NavItem[] = [
  {
    getTitle: m["nav.home"],
    href: localizeHref("/"),
  },
  {
    getTitle: m["nav.explorer"],
    href: localizeHref("/explorer"),
  },
  {
    getTitle: m["nav.upload"],
    href: localizeHref("/upload"),
  },
  {
    getTitle: m["nav.about"],
    href: "https://docs.uwcourses.com/about",
  },
];
