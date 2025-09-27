import { format, register } from "timeago.js";
import { getLocale } from "$lib/paraglide/runtime";
import ko from "timeago.js/lib/lang/ko";

// Register Korean (zh_CN and en_US are built-in)
register("ko", ko);

// Simple locale mapping
const localeMap = {
  en: "en_US",
  ko: "ko",
  zh: "zh_CN"
} as const;

/**
 * Format a date using timeago with the current locale
 */
export function formatTimeAgo(date: Date | string | number): string {
  const locale = getLocale();
  return format(date, localeMap[locale]);
}