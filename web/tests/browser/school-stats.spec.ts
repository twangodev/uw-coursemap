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
