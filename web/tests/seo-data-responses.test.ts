import { expect, it, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: false, dev: false }));
vi.mock("../../src/lib/server/data", () => ({ status: vi.fn() }));
import { handle } from "../../src/hooks.server";
import { status } from "../../src/lib/server/data";

it("excludes normalized instructor data requests from the HTML cache and indexing", async () => {
  // SvelteKit removes /__data.json from event.url before invoking handle.
  const url = new URL("https://uwcourses.com/instructors/HOBBES_LEGAULT");
  const response = await handle({
    event: {
      url,
      isDataRequest: true,
      request: new Request(url),
      platform: { env: {} },
    },
    resolve: async () =>
      new Response('{"type":"data"}', {
        headers: { "Content-Type": "application/json" },
      }),
  } as any);
  expect(status).not.toHaveBeenCalled();
  expect(response.headers.get("X-Robots-Tag")).toBe("noindex");
  expect(await response.json()).toEqual({ type: "data" });
});

it.each([
  ["/api/status", false, "noindex"],
  ["/", true, "noindex"],
  ["/courses/COMPSCI_300", false, null],
])(
  "sets the appropriate indexing header for %s (data request: %s)",
  async (path, isDataRequest, expected) => {
    const url = new URL(path, "https://uwcourses.com");
    const response = await handle({
      event: { url, isDataRequest, request: new Request(url) },
      resolve: async () => new Response("content"),
    } as any);
    expect(response.headers.get("X-Robots-Tag")).toBe(expected);
  },
);
