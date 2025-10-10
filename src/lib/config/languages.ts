import type { Locale } from "$lib/paraglide/runtime";
import type { Component } from "svelte";
import { Us, Cn, Kr } from "svelte-flag-icons";

export interface LanguageConfig {
  locale: Locale;
  nativeName: string;
  flag: Component;
  ogLocale: string;      // For og:locale (e.g., 'en_US')
  hrefLang: string;      // For hreflang (e.g., 'en-US')
}

export const languages: LanguageConfig[] = [
  {
    locale: "en",
    nativeName: "English",
    flag: Us,
    ogLocale: "en_US",
    hrefLang: "en-US",
  },
  {
    locale: "zh",
    nativeName: "中文",
    flag: Cn,
    ogLocale: "zh_CN",
    hrefLang: "zh-CN",
  },
  {
    locale: "ko",
    nativeName: "한국어",
    flag: Kr,
    ogLocale: "ko_KR",
    hrefLang: "ko-KR",
  },
];

// Helper function to get language config by locale
export function getLanguageConfig(locale: Locale): LanguageConfig | undefined {
  return languages.find(lang => lang.locale === locale);
}

// Helper to get og:locale format
export function getOgLocale(locale: Locale): string {
  return getLanguageConfig(locale)?.ogLocale || 'en_US';
}

// Helper to get hreflang format
export function getHrefLang(locale: Locale): string {
  return getLanguageConfig(locale)?.hrefLang || 'en-US';
}