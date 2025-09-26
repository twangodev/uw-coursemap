import type { Locale } from "$lib/paraglide/runtime.js";
import type { Component } from "svelte";
import { Us, Cn, Kr } from "svelte-flag-icons";

export interface LanguageConfig {
  locale: Locale;
  nativeName: string;
  flag: Component;
}

export const languages: LanguageConfig[] = [
  {
    locale: "en",
    nativeName: "English",
    flag: Us,
  },
  {
    locale: "zh",
    nativeName: "中文",
    flag: Cn,
  },
  {
    locale: "ko",
    nativeName: "한국어",
    flag: Kr,
  },
];