import { expect, it } from "vitest";
import { errorPresentation } from "../../src/lib/error-presentation";
it("offers recovery suited to missing pages, rate limits and server failures", () => {
  expect(errorPresentation(404)).toMatchObject({
    label: "Not Found",
    retry: false,
  });
  expect(errorPresentation(410)).toMatchObject({ label: "Gone", retry: false });
  expect(errorPresentation(429).retry).toBe(true);
  expect(errorPresentation(503)).toMatchObject({
    label: "Service Unavailable",
    retry: true,
  });
  expect(errorPresentation(502)).toMatchObject({
    label: "Bad Gateway",
    retry: true,
  });
  expect(errorPresentation(599)).toMatchObject({
    label: "Unexpected error",
    retry: true,
  });
});
