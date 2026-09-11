import { expect, it, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: false }));
import { load as subjects } from "../../src/routes/subjects/+page.server";
import { load as departmentStats } from "../../src/routes/stats/[subject]/+page.server";

it.each([
  ["/subjects", "/departments", subjects],
  ["/stats/COMPSCI", "/departments/COMPSCI", departmentStats],
])(
  "prerenders the %s redirect without reading query parameters",
  (path, destination, load) => {
    const url = new URL(path, "https://uwcourses.com");
    Object.defineProperty(url, "search", {
      get() {
        throw new Error("Cannot access url.search during prerendering");
      },
    });
    expect(() => load({ url, params: { subject: "COMPSCI" } } as any)).toThrow(
      expect.objectContaining({ status: 308, location: destination }),
    );
  },
);
