import { expect, test } from "@playwright/test";

test("original instructor URLs retain profile identity and term filtering", async ({
  page,
  request,
}) => {
  await page.goto("/instructors/HOBBES_LEGAULT?term=1264");
  await expect(page).toHaveURL(/HOBBES_LEGAULT\?term=1264$/);
  await expect(
    page.getByRole("heading", { name: "Hobbes Legault", exact: true }),
  ).toBeVisible();
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://uwcourses.com/instructors/HOBBES_LEGAULT",
  );
  const response = await request.get(
    "/instructors/instructor_a65e64df990aa3bab98ee125?term=1264",
    { maxRedirects: 0 },
  );
  expect(response.status()).toBe(308);
  expect(response.headers().location).toBe(
    "/instructors/HOBBES_LEGAULT?term=1264",
  );
  expect((await request.get("/instructors/DOES_NOT_EXIST")).status()).toBe(404);
});

test("old directory and department addresses redirect to their canonical URLs", async ({
  page,
}) => {
  for (const path of ["/departments", "/stats", "/subjects"]) {
    await page.goto(path);
    await expect(
      page.getByRole("heading", { name: "Departments", exact: true }),
    ).toBeVisible();
    expect(new URL(page.url()).pathname).toBe("/departments");
  }
  for (const path of ["/departments/COMPSCI", "/stats/COMPSCI"]) {
    await page.goto(path);
    await expect(
      page.getByRole("heading", { name: "Computer Sciences", exact: true }),
    ).toBeVisible();
    expect(new URL(page.url()).pathname).toBe("/departments/COMPSCI");
  }
  await page.goto("/explorer/all");
  await expect(
    page.getByRole("heading", { name: "Course prerequisite map", exact: true }),
  ).toBeVisible();
  await page.goto("/instructors/by-rating-count");
  await expect(
    page.getByRole("heading", { name: "Find a professor", exact: true }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByLabel("Search instructors").fill("Hobbes");
  await page
    .locator(".instructor-search")
    .getByRole("button", { name: "Search", exact: true })
    .click();
  await expect(page).toHaveURL(/instructors\/by-rating-count\?.*q=Hobbes/);
  await expect(page.locator(".course-row").first()).toHaveAttribute(
    "href",
    "/instructors/HOBBES_LEGAULT",
  );
});
