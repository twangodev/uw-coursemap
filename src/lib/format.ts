export function normalize(value: string) {
  return value
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .replace(/^CS(?=\d)/, "COMPSCI");
}
export function termName(value: string) {
  const n = Number(value);
  if (!/^1\d{3}$/.test(value)) return value;
  const year = 1900 + Math.floor(n / 10);
  const season: Record<string, string> = {
    "2": "Fall",
    "4": "Spring",
    "6": "Summer",
  };
  return `${season[value.slice(-1)] || "Term"} ${value.endsWith("2") ? year - 1 : year}`;
}
export function credits(min: number | null, max: number | null) {
  return min == null
    ? "Credits unavailable"
    : `${min}${max != null && max !== min ? "–" + max : ""} credits`;
}
export function courseSlug(code: string) {
  const split = code.lastIndexOf(" ");
  const subject = code.slice(0, split).split("/")[0].toLowerCase();
  const department = subject === "compsci" ? "cs" : subject;
  return `${department.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}-${code.slice(split + 1)}`;
}
export function courseUrl(uid: string, code?: string | null) {
  return "/courses/" + encodeURIComponent(code ? courseSlug(code) : uid);
}
export function instructorUrl(uid: string) {
  return "/instructors/" + encodeURIComponent(uid);
}
export function safeUrl(value: unknown): string | undefined {
  if (typeof value !== "string") return;
  try {
    const u = new URL(value);
    if (u.protocol === "https:" || u.protocol === "http:") return u.href;
  } catch {}
}

/** Present all-caps catalog headings without changing the source record. */
export function courseTitle(value: string) {
  if (value !== value.toUpperCase()) return value;
  const keep =
    /^(?:[IVX]+|AI|DNA|RNA|GIS|GPS|SQL|HTML|CSS|CAD|CAM|MRI|NMR|ESL|STEM|R|C|C\+\+|UW|US|USA|LGBTQ\+?|HIV|AIDS)$/;
  const small = new Set([
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
  ]);
  return value
    .split(/(\s+)/)
    .map((word, index) => {
      if (keep.test(word) || !word.trim()) return word;
      const lower = word.toLowerCase();
      return index && small.has(lower)
        ? lower
        : lower.replace(/^\w/, (letter) => letter.toUpperCase());
    })
    .join("");
}
