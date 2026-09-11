import Negotiator from "negotiator";

/** Prefer HTML for wildcard requests; explicit media types follow Accept weights. */
export function negotiatedFormat(
  accept: string | null,
): "html" | "md" | "json" {
  const type = new Negotiator({
    headers: { accept: accept ?? "*/*" },
  }).mediaType(["text/html", "text/markdown", "application/json"]);
  return type === "text/markdown"
    ? "md"
    : type === "application/json"
      ? "json"
      : "html";
}
