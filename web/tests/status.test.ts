import { expect, test, vi } from "vitest";
vi.mock("../../src/lib/server/runtime", () => ({
  building: false,
  dev: false,
}));
import { status } from "../../src/lib/server/data";
import { interactionSchemas } from "../../src/lib/api/schemas";

test("status exposes the running website commit independently of the cached dataset", async () => {
  const platform = {
    env: {
      SITE_COMMIT: "current-website",
      DEPLOYED_AT: "2026-09-10T00:00:00Z",
    },
  } as App.Platform;
  const result = interactionSchemas.Status.parse(await status(platform));
  expect(result.site_commit).toBe("current-website");
  expect(result.deployed_at).toBe("2026-09-10T00:00:00Z");
  expect(result.revision).toMatch(/^[a-f0-9]{40}$/);
  expect((await status()).site_commit).toBeNull();
});
