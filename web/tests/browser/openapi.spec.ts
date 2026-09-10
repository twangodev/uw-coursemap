import { expect, test } from "@playwright/test";

test("OpenAPI mounts one viewer with documentation above the fold", async ({
  page,
}) => {
  await page.goto("/openapi");
  await expect(page.locator("body > [data-v-app]")).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: "UW Courses document API", exact: true }),
  ).toBeInViewport({ timeout: 30000 });
  await expect(
    page.getByRole("link", { name: "OpenAPI JSON ↗" }),
  ).toHaveAttribute("href", "/openapi.json");
});
