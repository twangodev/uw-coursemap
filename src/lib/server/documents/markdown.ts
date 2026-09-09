import { unified } from "unified";
import remarkGfm from "remark-gfm";
import remarkStringify from "remark-stringify";
import type { Root, RootContent } from "mdast";

const label = (key: string) =>
  key.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ");
const text = (value: unknown) => ({
  type: "text" as const,
  value: String(value),
});
const inline = (value: unknown) =>
  typeof value === "string" && /^(https?:\/\/|\/data\/)/.test(value)
    ? {
        type: "link" as const,
        url: new URL(value, "https://uwcourses.com").href,
        children: [text(value)],
      }
    : text(value);
/** Lossless readable rendering of the public payload, including nested citations. */
export function documentMarkdown(document: {
  title: string;
  url: string;
  data: unknown;
  dataset: unknown;
}) {
  const children: RootContent[] = [
    { type: "heading", depth: 1, children: [text(document.title)] },
    {
      type: "paragraph",
      children: [
        {
          type: "link",
          url: document.url,
          children: [text("View on UW Courses")],
        },
      ],
    },
  ];
  function append(name: string, value: unknown, depth: number) {
    if (value === null || value === undefined) return;
    children.push({
      type: "heading",
      depth: Math.min(depth, 6) as 2,
      children: [text(label(name))],
    });
    if (Array.isArray(value)) {
      if (!value.length) {
        children.push({
          type: "paragraph",
          children: [text("None recorded.")],
        });
        return;
      }
      if (value.every((item) => typeof item !== "object" || item === null)) {
        children.push({
          type: "list",
          ordered: false,
          spread: false,
          children: value.map((item) => ({
            type: "listItem",
            spread: false,
            children: [{ type: "paragraph", children: [inline(item)] }],
          })),
        });
      } else if (
        value.every(
          (item) =>
            item && typeof item === "object" && typeof item.text === "string",
        )
      ) {
        for (const claim of value) {
          children.push({ type: "paragraph", children: [text(claim.text)] });
          const { text: _text, ...evidence } = claim;
          if (Object.keys(evidence).length)
            children.push({
              type: "code",
              lang: "json",
              value: JSON.stringify(evidence, null, 2),
            });
        }
      } else {
        // Tables are compact for records with scalar fields; nested records retain all fields as JSON.
        const keys = [
          ...new Set(
            value.flatMap((item) =>
              item && typeof item === "object" ? Object.keys(item) : [],
            ),
          ),
        ];
        if (
          keys.length &&
          keys.length <= 12 &&
          value.every(
            (item) =>
              item &&
              Object.values(item).every(
                (v) => v === null || typeof v !== "object",
              ),
          )
        ) {
          children.push({
            type: "table",
            children: [
              keys,
              ...value.map((item) => keys.map((k) => item[k] ?? "")),
            ].map((row) => ({
              type: "tableRow",
              children: row.map((cell) => ({
                type: "tableCell",
                children: [text(cell)],
              })),
            })),
          });
        } else
          children.push({
            type: "code",
            lang: "json",
            value: JSON.stringify(value, null, 2),
          });
      }
    } else if (typeof value === "object") {
      for (const [key, item] of Object.entries(value))
        append(key, item, depth + 1);
    } else children.push({ type: "paragraph", children: [inline(value)] });
  }
  append("Dataset", document.dataset, 2);
  for (const [key, value] of Object.entries(
    document.data as Record<string, unknown>,
  ))
    append(key, value, 2);
  return unified()
    .use(remarkGfm)
    .use(remarkStringify)
    .stringify({ type: "root", children } satisfies Root);
}
