import { expect, test } from "@playwright/test";
import { documentSchemas } from "../../../src/lib/api/schemas";

test("statistics documents negotiate formats and select historical terms", async ({
  request,
}) => {
  const response = await request.get("/stats.json");
  expect(response.status()).toBe(200);
  const document = await response.json();
  expect(documentSchemas.Statistics.safeParse(document).success).toBe(true);
  const stats = document.data.schoolStats;
  expect(stats.selectedTerm).toBe(document.dataset.term);
  const earlier = Object.keys(stats.terms)
    .filter((t) => t < stats.selectedTerm && stats.terms[t].gradeCount > 0)
    .sort()
    .at(-1)!;
  const selected = await (
    await request.get(`/stats.json?term=${earlier}`)
  ).json();
  expect(selected.data.schoolStats.selectedTerm).toBe(earlier);
  expect(
    (await (await request.get("/stats.json")).json()).data.schoolStats
      .selectedTerm,
  ).toBe(document.dataset.term);
  const md = await request.get(`/stats?term=${earlier}`, {
    headers: { Accept: "text/markdown" },
  });
  expect(md.headers()["content-type"]).toContain("text/markdown");
  expect(await md.text()).toContain("school Stats");
  expect(md.headers().vary.toLowerCase()).toContain("accept");
  expect((await request.get("/stats.json?term=bad")).status()).toBe(400);
});

test("statistics are readable on mobile and respond to term changes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/stats");
  await expect(
    page.getByRole("heading", { name: "UW–Madison, by the numbers." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "The rhythm of campus" }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Previous term" }).click();
  await expect(page).toHaveURL(/stats\?term=/);
  await expect(
    page.getByText("We don’t have a building schedule", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next term" }).click();
  await expect(page.locator(".heatmap")).toBeVisible();
  await page.locator(".heatmap button").first().focus();
  await expect(page.locator(".heat-detail")).toContainText(
    "meetings across the recorded term",
  );
  const building = page.locator('.map svg [role="button"]').first();
  await building.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".map .caption")).toContainText(
    "scheduled enrollment visits",
  );
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://uwcourses.com/stats",
  );
});

test("academic charts drill into subjects, find courses, and preserve historical labels", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 1280, height: 1000 });
  const doc = await (await request.get("/stats.json")).json();
  const term = doc.data.schoolStats.academics.term;
  await page.goto(`/stats?term=${term}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(
    page.getByText("courses with recorded grades", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "What does Madison study?" }),
  ).toBeVisible();
  const tree = page.locator(".treemap");
  const first = tree.getByRole("button").first();
  await first.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "← All subjects" }),
  ).toBeVisible();
  await expect(tree.locator("a").first()).toHaveAttribute(
    "href",
    /^\/courses\//,
  );
  await page.getByRole("button", { name: "← All subjects" }).click();
  const dot = page.locator('.dot-chart circle[tabindex="0"]');
  await expect(dot).toHaveCount(1);
  const previousDot = await dot.getAttribute("aria-label");
  await dot.focus();
  await page.keyboard.press("ArrowRight");
  await expect(dot).not.toHaveAttribute("aria-label", previousDot!);
  await page.getByLabel("Find a course in the dot plot").fill("CS 300");
  await expect(page.locator(".dot-detail")).toContainText("COMPSCI 300");
  await expect(page.locator(".dot-detail a")).toHaveAttribute(
    "href",
    "/courses/COMPSCI_300",
  );
  await page.locator(".rank-legend button").first().click();
  await expect(page.locator(".rank-legend button").first()).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBe(true);
  await expect(
    page.getByRole("heading", { name: "How the grade mix has changed" }),
  ).toBeVisible();
});
