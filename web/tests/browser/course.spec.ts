import { test, expect } from "@playwright/test";
const uid = "course_28c3390ba944d49fd17f7c72";
test("course reading, citations, graph and theme", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(
    page.getByRole("heading", { name: "PROGRAMMING II", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Java", { exact: false }).first()).toBeVisible();
  await page
    .getByRole("button", { name: "Explore prerequisite graph" })
    .click();
  await expect(page.locator(".svelte-flow")).toBeVisible();
  await page.getByLabel("Color theme").selectOption("dark");
  await expect(page.locator("html")).toHaveClass("dark");
  await page.getByText("Full model traces", { exact: true }).click();
  await expect(page.getByText("Download part 1").last()).toBeVisible();
  await page.screenshot({
    path: "test-results/cs300-dark.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("search resolves aliases and exposes filters", async ({ page }) => {
  await page.goto("/search?q=CS300");
  await expect(page.locator(".course-row").first()).toContainText(
    "COMPSCI 300",
  );
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByLabel("Search", { exact: true }).fill("programming");
  await expect(page.locator(".course-row").first()).toBeVisible();
});
test("mobile layout stays within viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({
    path: "test-results/cs300-mobile.png",
    fullPage: true,
  });
});
test("course content is available without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:4173/courses/${uid}`);
  await expect(
    page.getByRole("heading", { name: "PROGRAMMING II", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Prerequisite text tree", { exact: true }),
  ).toBeVisible();
  await context.close();
});

test("grade filters reset and instructor links retain course context", async ({
  page,
}) => {
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const grades = page.locator("#grades");
  const count = grades.locator("p").filter({ hasText: "letter grades" });
  const overall = await count.textContent();
  const instructors = grades.getByRole("combobox", {
    name: "Instructor",
    exact: true,
  });
  const option = await instructors
    .locator("option")
    .nth(1)
    .getAttribute("value");
  const response = page.waitForResponse(
    (r) => r.url().includes(`/api/courses/${uid}/grades`) && r.ok(),
  );
  await instructors.selectOption(option!);
  await response;
  await expect(grades.getByText("Loading grades…")).not.toBeVisible();
  await instructors.selectOption("");
  await expect(count).toHaveText(overall!);
  const professor = page.locator("#professors h3 a").first();
  const name = await professor.textContent();
  await professor.click();
  await expect(
    page.getByRole("heading", { name: name!, exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Recorded teaching history" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/instructor.png",
    fullPage: true,
  });
});

test("home and cross-listed course render on desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Find your next class." }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/home.png", fullPage: true });
  await page.goto("/courses/course_63e805b33518ff3fd8dc0a39");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(page.locator("h1")).toContainText("HIGH PERFORMANCE COMPUTING");
  await page.locator("#grades").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "test-results/cs759.png", fullPage: true });
});
