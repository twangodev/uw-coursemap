import { expect, it } from "vitest";
import {
  representation,
  representationUrl,
  alternateLinks,
} from "../../src/lib/documents";
import { documentMarkdown } from "../../src/lib/server/documents/markdown";
import {
  responseCacheKey,
  cachedResponse,
} from "../../src/lib/server/response-cache";

it("maps document suffixes without intercepting assets or Svelte transport", () => {
  expect(representation("/index.md")).toEqual({ path: "/", format: "md" });
  expect(representation("/courses/COMPSCI_300.json")).toEqual({
    path: "/courses/COMPSCI_300",
    format: "json",
  });
  for (const path of [
    "/data/courses.json",
    "/api/search.json",
    "/courses/COMPSCI_300/__data.json",
    "/foo.json",
  ])
    expect(representation(path)).toBeNull();
  expect(representationUrl("/search", "md", "?q=java")).toBe(
    "/search.md?q=java",
  );
  expect(alternateLinks("/")).toContain("/index.json");
});
it("preserves evidence and escapes untrusted Markdown text", () => {
  const md = documentMarkdown({
    title: "<script>title</script>",
    url: "https://uwcourses.com/courses/COMPSCI_300",
    dataset: { revision: "abc" },
    data: {
      summary: "Java **not a command**",
      grades: [{ term: "1272", a: 10 }],
      evidence: [
        {
          model: "nvidia/qwen",
          citations: [
            {
              source_review_id: "review-123",
              source_url: "https://example.com",
            },
          ],
        },
      ],
    },
  });
  expect(md).toContain("review-123");
  expect(md).toContain("nvidia/qwen");
  expect(md).toContain("| term");
  expect(md).not.toContain("# <script>");
});
it("separates releases, formats, query variants and user cache-like parameters", () => {
  const key = (path: string, release = "one") =>
    responseCacheKey(new URL(path, "https://uwcourses.com"), release).url;
  expect(
    new Set([
      key("/search"),
      key("/search.md"),
      key("/search.json"),
      key("/search?q=java"),
      key("/search?_release=two"),
      key("/search", "two"),
    ]).size,
  ).toBe(6);
});
it("caches successful documents, revalidates, and bypasses navigation and credentials", async () => {
  const entries = new Map<string, Response>();
  const original = globalThis.caches;
  Object.defineProperty(globalThis, "caches", {
    configurable: true,
    value: {
      default: {
        match: async (key: Request) => entries.get(key.url)?.clone(),
        put: async (key: Request, value: Response) => {
          entries.set(key.url, value);
        },
      },
    },
  });
  try {
    let calls = 0;
    const writes: Promise<unknown>[] = [];
    const event: any = {
      url: new URL("https://uwcourses.com/search.json?q=java"),
      request: new Request("https://uwcourses.com/search.json?q=java"),
      platform: {
        env: { SITE_COMMIT: "a", DATA_PROJECTION: "b", DATA_SLOT: "a" },
        context: { waitUntil: (p: Promise<unknown>) => writes.push(p) },
      },
      isDataRequest: false,
    };
    const render = async () => {
      calls++;
      return new Response("body");
    };
    const miss = await cachedResponse(event, render);
    await Promise.all(writes);
    expect(miss.headers.get("x-cache")).toBe("MISS");
    expect((await cachedResponse(event, render)).headers.get("x-cache")).toBe(
      "HIT",
    );
    expect(calls).toBe(1);
    event.request = new Request(event.url, {
      headers: { "If-None-Match": miss.headers.get("etag")! },
    });
    expect((await cachedResponse(event, render)).status).toBe(304);
    event.isDataRequest = true;
    await cachedResponse(event, render);
    expect(calls).toBe(2);
    event.isDataRequest = false;
    event.request = new Request(event.url, {
      headers: { Cookie: "session=x" },
    });
    await cachedResponse(event, render);
    expect(calls).toBe(3);
  } finally {
    Object.defineProperty(globalThis, "caches", {
      configurable: true,
      value: original,
    });
  }
});
