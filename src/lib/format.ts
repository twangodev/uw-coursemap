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
export function courseUrl(uid: string) {
  return "/courses/" + encodeURIComponent(uid);
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
