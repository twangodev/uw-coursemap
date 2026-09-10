import { expect, test, vi } from "vitest";
vi.mock("$app/environment", () => ({ dev: false }));
import { GET } from "../../src/routes/api/weather/+server";

test("cached weather permits the response headers added by server hooks", async () => {
  const cached = await fetch('data:application/json,{"available":false}');
  expect(() => cached.headers.set("X-Robots-Tag", "noindex")).toThrow();
  vi.stubGlobal("caches", { default: { match: async () => cached } });
  try {
    const result = await GET({
      platform: {},
      url: new URL("https://uwcourses.com/api/weather"),
    } as Parameters<typeof GET>[0]);
    result.headers.set("X-Robots-Tag", "noindex");
    expect(result.status).toBe(200);
    expect(await result.json()).toEqual({ available: false });
  } finally {
    vi.unstubAllGlobals();
  }
});
