/** Canonical, public document URLs; assets and internal APIs are excluded. */
export function documentPath(path: string) {
  return path.replace(/\/$/, "") || "/";
}
export function representationUrl(
  path: string,
  format: "md" | "json",
  search = "",
) {
  const canonical = documentPath(path);
  return (canonical === "/" ? "/index" : canonical) + "." + format + search;
}
export function representation(path: string) {
  const match = path.match(/^(.*)\.(md|json)$/);
  if (!match || path.includes("/__data.json")) return null;
  const canonical = match[1] === "/index" ? "/" : match[1];
  return isDocument(canonical)
    ? { path: canonical, format: match[2] as "md" | "json" }
    : null;
}
export function isDocument(path: string) {
  return /^(\/|\/search|\/departments(?:\/[^/.]+(?:\/(?:catalog|easiest|hardest))?)?|\/courses\/[^/.]+|\/instructors\/[^/.]+|\/explorer(?:\/[^/.]+)?)$/.test(
    path,
  );
}
export function alternateLinks(path: string, search = "") {
  return (
    [
      ["md", "text/markdown"],
      ["json", "application/json"],
    ] as const
  )
    .map(
      ([format, type]) =>
        `<https://uwcourses.com${representationUrl(path, format, search)}>; rel="alternate"; type="${type}"`,
    )
    .join(", ");
}
