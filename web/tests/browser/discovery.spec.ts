import { test, expect } from "@playwright/test";
const instructor = "instructor_a65e64df990aa3bab98ee125";
test("department overview stays historical while finder and term statistics change", async ({
  page,
}) => {
  await page.goto("/explorer/COMPSCI");
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
test("dedicated course collections preserve department filters and fixed rankings", async ({ page }) => {
  await page.goto("/explorer/COMPSCI");
  await page.getByRole("navigation", { name: "Course collections" }).getByRole("link", { name: "Easiest courses" }).click();
  await expect(page).toHaveURL(/\/explorer\/COMPSCI\/easiest/);
  await expect(page.getByRole("heading", { name: "Easiest courses in Computer Sciences", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Department", exact: true })).toHaveCount(0);
  await expect(page.locator(".discovery-card").first()).toContainText("#1");
  await expect(page.getByRole("button", { name: "Sort courses", exact: true })).toHaveCount(0);
  await page.getByRole("navigation", { name: "Course collections" }).getByRole("link", { name: "Hardest courses" }).click();
  await expect(page).toHaveURL(/\/explorer\/COMPSCI\/hardest/);
  await expect(page.getByRole("heading", { name: "Hardest courses in Computer Sciences", exact: true })).toBeVisible();
  await expect(page.locator(".discovery-card").first()).toContainText("COMPSCI");
  await page.reload();
  await expect(page.getByRole("button", { name: "Department", exact: true })).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});


test("department rankings are available without JavaScript and cannot switch subjects through query parameters", async ({ browser, page }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const staticPage = await context.newPage();
  await staticPage.goto("http://127.0.0.1:4173/explorer/COMPSCI/easiest");
  await expect(staticPage.getByRole("heading", { name: "Easiest courses in Computer Sciences", exact: true })).toBeVisible();
  await expect(staticPage.locator(".discovery-card").first()).toContainText("COMPSCI");
  await context.close();
  await page.goto("/explorer/COMPSCI/easiest?subject=MATH&ranking=hardest");
  await expect(page.locator(".discovery-card").first()).toContainText("COMPSCI");
  await expect(page.getByRole("heading", { name: "Easiest courses in Computer Sciences", exact: true })).toBeVisible();
  const response = await page.goto("/explorer/NOTADEPARTMENT/easiest");
  expect(response?.status()).toBe(404);
});

test("main navigation opens the instructor directory on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "instructors", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Find a professor", exact: true })).toBeVisible();
  await expect(page.getByLabel("Search instructors")).toBeVisible();
  await expect(page.locator(".course-row").first()).toContainText("adjusted");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});


test("department names appear in search, headings and SEO metadata", async ({ page }) => {
  await page.goto("/subjects");
  await page.getByLabel("Find a department").fill("computer sciences");
  const link = page.locator('.department-grid a[href="/explorer/COMPSCI"]');
  await expect(link).toContainText("Computer Sciences");
  await link.click();
  await expect(page.getByRole("heading", { name: "Computer Sciences", exact: true })).toBeVisible();
  await expect(page).toHaveTitle("Computer Sciences (COMPSCI) Courses, Grades & Reviews · UW Courses");
  await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /Explore Computer Sciences courses at UW–Madison/);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
