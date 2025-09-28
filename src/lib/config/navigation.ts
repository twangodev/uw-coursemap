import type { NavItem } from "$lib/types/nav.ts";
import { m } from "$lib/paraglide/messages";
import { localizeHref } from "$lib/paraglide/runtime";

export const navigation: NavItem[] = [
  {
    getTitle: m["nav.home"],
    href: "/",
  },
  {
    getTitle: m["nav.explorer"],
    href: "/explorer",
  },
  {
    getTitle: m["nav.upload"],
    href: "/upload",
  },
  {
    getTitle: m["nav.about"],
    href: "https://docs.uwcourses.com/about",
  },
];

export function getLocalizedNavigation(): NavItem[] {
  return navigation.map(item => ({
    ...item,
    href: item.href.startsWith('http') ? item.href : localizeHref(item.href)
  }));
}
