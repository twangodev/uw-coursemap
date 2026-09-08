import { expect, test } from "@playwright/test";

test("canonical course URLs render and cross-list aliases redirect without supporting raw IDs", async ({
  page,
  request,
}) => {
  const old = await request.get(
    "/courses/course_28c3390ba944d49fd17f7c72?from=bookmark",
    { maxRedirects: 0 },
  );
  expect(old.status()).toBe(404);
  for (const alias of ["CS300", "compsci-300"]) {
    const response = await request.get(`/courses/${alias}`, {
      maxRedirects: 0,
    });
    expect(response.status()).toBe(308);
    expect(response.headers().location).toBe("/courses/cs-300");
  }
  const crosslist = await request.get("/courses/ece-759", { maxRedirects: 0 });
  expect(crosslist.status()).toBe(308);
  expect(crosslist.headers().location).toBe("/courses/cs-759");
  const response = await page.goto("/courses/cs-300");
  expect(response?.status()).toBe(200);
  await expect(page).toHaveURL(/\/courses\/cs-300$/);
  await expect(
    page.getByRole("heading", { name: "Programming II", exact: true }),
  ).toBeVisible();
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "/courses/cs-300",
  );
  expect((await request.get("/courses/nonexistent-999")).status()).toBe(404);
});

test("course lists link directly to readable pages", async ({ page }) => {
  await page.goto("/search?q=CS300");
  const link = page
    .locator(".discovery-card")
    .first()
    .locator(".card-heading a");
  await expect(link).toHaveAttribute("href", "/courses/cs-300");
  await link.click();
  await expect(page).toHaveURL(/\/courses\/cs-300$/);
});
