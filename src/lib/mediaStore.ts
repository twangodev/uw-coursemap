import { writable } from "svelte/store";
import { browser } from "$app/environment";

export const isDesktop = writable(false);

if (browser) {
  const mediaQuery = window.matchMedia("(min-width: 768px)");
  isDesktop.set(mediaQuery.matches);
  mediaQuery.addEventListener("change", (e) => isDesktop.set(e.matches));
}
