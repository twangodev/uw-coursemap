import { expect, test } from "@playwright/test";
test("course history charts expand on demand for an ungraded current term", async ({
  page,
}) => {
  await page.goto("/courses/COMPSCI_300");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const history = page.getByRole("region", {
    name: "Historical grade outcomes",
  });
  await expect(history).toHaveCount(0);
  await page.locator(".more-grade-details > summary").click();
  await history.scrollIntoViewIfNeeded();
  await expect(
    history.getByRole("heading", { name: "Grade mix over time" }),
  ).toBeVisible();
  await expect(
    history.getByRole("heading", { name: "Recorded grades by term" }),
  ).toBeVisible();
  await expect(history.locator("svg").first()).toBeVisible();
  await page
    .getByText("Grade counts & non-letter outcomes", { exact: true })
    .click();
  await expect(page.locator(".outcomes-table")).toContainText("Spring 2026");
  await page.locator(".more-grade-details > summary").click();
  await expect(history).toHaveCount(0);
  await page.locator(".more-grade-details > summary").click();
  await expect(history.locator("svg").first()).toBeVisible();
});
test("departments and prerequisite maps serve distinct purposes", async ({
  page,
}) => {
  await page.goto("/departments/COMPSCI");
  await expect(
    page.getByRole("heading", { name: "Computer Sciences", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Explore prerequisite map" }).click();
  await expect(page).toHaveURL(/explorer\/COMPSCI$/);
  await expect(
    page.getByRole("heading", { name: "Computer Sciences prerequisite map" }),
  ).toBeVisible();
  await expect(page.locator(".map")).toHaveAttribute("data-ready", "true", { timeout: 30000 });
  const count = Number(await page.locator(".map").getAttribute("data-node-count"));
  expect(count).toBeGreaterThan(100);
  expect(await page.locator(".map").evaluate(el => { const r = el.getBoundingClientRect(); return r.width === innerWidth && r.height === innerHeight; })).toBe(true);
  await page.getByLabel("Find a course on the map").fill("COMPSCI 400");
  await page.getByRole("button", { name: "COMPSCI 400", exact: true }).click();
  await expect(page.getByRole("complementary", { name: "Selected course" })).toContainText("COMPSCI 400");
  await expect(page.locator(".map")).toHaveAttribute("data-node-count", String(count));
  await page.getByRole("button", { name: "Fit all courses", exact: true }).click();
  await expect(page.getByRole("complementary", { name: "Selected course" })).toHaveCount(0);
  await page
    .getByRole("link", { name: "Department courses & statistics" })
    .click();
  await expect(page).toHaveURL(/departments\/COMPSCI$/);
});
