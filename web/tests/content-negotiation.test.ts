import { expect, it } from "vitest";
import { negotiatedFormat } from "../../src/lib/server/content-negotiation";

it.each([
  [null, "html"],
  ["*/*", "html"],
  ["text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "html"],
  ["text/markdown", "md"],
  ["application/json", "json"],
  ["text/markdown, text/html;q=0.5", "md"],
  ["text/markdown;q=0.1, text/html;q=0.9", "html"],
  ["text/markdown;q=0, */*", "html"],
  ["text/html;q=0, text/*;q=0.8", "md"],
  ["application/json;q=0.9,text/markdown;q=0.5", "json"],
  ["image/png", "html"],
])("negotiates %s as %s", (accept, expected) => {
  expect(negotiatedFormat(accept)).toBe(expected);
});
