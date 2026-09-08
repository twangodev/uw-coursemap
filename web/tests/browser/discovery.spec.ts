import { test, expect } from "@playwright/test";
const instructor = "instructor_a65e64df990aa3bab98ee125";
test("department overview stays historical while finder and term statistics change", async ({
  page,
}) => {
  await page.goto("/subjects/COMPSCI");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const overview = page.getByRole("region", {
    name: "Department overview",
    exact: true,
  });
  await expect(overview).toContainText("How grades break down");
  const before = await overview
    .locator('[role="img"]')
    .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("aria-label")));
  await expect(page.locator(".discovery-card").first()).toContainText(
    "Offering recorded · Fall 2026",
  );
  await overview.screenshot({
    animations: "disabled",
    path: "/tmp/uw-coursemap-design-audit/department-overview.png",
  });
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "Spring 2026", exact: true }).click();
  await expect(
    page
      .getByRole("region", { name: "Selected-term department statistics" })
      .first(),
  ).toContainText("Spring 2026");
  expect(
    await overview
      .locator('[role="img"]')
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("aria-label"))),
  ).toEqual(before);
  await page
    .getByRole("button", { name: "Course availability", exact: true })
    .click();
  await page.getByRole("option", { name: "Full catalog", exact: true }).click();
  await expect(page.locator(".discovery-card").first()).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
});
test("instructor reviews show original comments, paginate and filter by course", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`/instructors/${instructor}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const reviews = page.locator(".student-reviews");
  await expect(reviews.locator(".student-review")).toHaveCount(6);
  await expect(reviews).toContainText("Original student reviews");
  await reviews.screenshot({
    animations: "disabled",
    path: "/tmp/uw-coursemap-design-audit/instructor-reviews.png",
  });
  await reviews
    .getByRole("button", { name: "Read more reviews", exact: true })
    .click();
  await expect(reviews.locator(".student-review")).toHaveCount(12);
  await page
    .getByRole("button", { name: "Reviews for course", exact: true })
    .click();
  await page.getByRole("option", { name: "COMPSCI 300", exact: true }).click();
  await expect(reviews.locator(".student-review")).toHaveCount(6);
  await expect(reviews.locator(".review-meta").first()).toContainText(
    "COMPSCI 300",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  expect(errors).toEqual([]);
});
test("legacy easiest URL becomes a historical-grade course finder", async ({
  page,
}) => {
  await page.goto("/courses/easiest");
  await expect(page).toHaveURL(/\/search\?sort=gpa/);
  await expect(page.locator(".discovery-card").first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Sort courses", exact: true }),
  ).toContainText("Higher historical grades");
  await expect(page.locator(".route-content")).toHaveCSS("opacity", "1");
  await page.locator(".discovery-card").first().screenshot({
    animations: "disabled",
    path: "/tmp/uw-coursemap-design-audit/course-finder-card.png",
  });
});
