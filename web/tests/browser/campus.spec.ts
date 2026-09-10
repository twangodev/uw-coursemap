import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";

const date = JSON.parse(readFileSync(".site/campus.json", "utf8")).from;
const now = new Date(`${date}T15:00:00Z`);
async function mockCampus(page: import("@playwright/test").Page) {
  await page.route(`**/campus/**${date}.json`, (route) =>
    route.fulfill({
      json: {
        date,
        events: [
          [+now - 60000, 100, 0],
          [+now + 600000, 20, 0],
          [+now + 3600000, 0, 120],
        ],
        enrollmentEvents: [
          [+now - 60000, 20372, 0, 95, 0],
          [+now + 3600000, 0, 20372, 0, 95],
        ],
      },
    }),
  );
  await page.route("**/api/weather", (route) =>
    route.fulfill({
      json: {
        available: true,
        temperatureF: 72,
        description: "Fair",
        observedAt: "2026-09-10T14:45:00Z",
        source: "National Weather Service · KMSN",
        sourceUrl: "https://www.weather.gov/wrh/timeseries?site=KMSN",
      },
    }),
  );
}

test("campus facts show estimated enrollment over a local map, with accessible context", async ({
  page,
}) => {
  await page.clock.setFixedTime(now);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockCampus(page);
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText(
    new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Chicago",
      hour: "numeric",
      minute: "2-digit",
    }).format(now),
  );
  await expect(scene).toContainText("students scheduled in class right now");
  await expect(
    scene.getByRole("img", { name: "20,350", exact: true }),
  ).toBeVisible();
  await expect(scene.locator(".campus-map")).toBeVisible();
  await scene.getByRole("button", { name: "About this campus fact" }).click();
  await expect(page.getByRole("tooltip")).toContainText("not live attendance");
  await page.keyboard.press("Escape");
  await scene.getByRole("button", { name: "Next campus fact" }).click();
  await expect(scene).toContainText("classes in session right now");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole("combobox", { name: "Search courses or topics" }),
  ).toBeVisible();
});

test("campus facts rotate and can be paused", async ({ page }) => {
  await page.clock.install({ time: now });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await mockCampus(page);
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("students scheduled in class right now");
  await page.clock.fastForward(8500);
  await expect(scene).toContainText("classes in session right now");
  await scene.getByRole("button", { name: "Pause campus facts" }).click();
  await page.mouse.move(0, 0);
  await page.getByRole("heading", { level: 1 }).click();
  await page.clock.fastForward(17000);
  await expect(scene).toContainText("classes in session right now");
});

test("out-of-coverage dates use solar facts without inventing attendance", async ({
  page,
}) => {
  await page.clock.install({ time: new Date("2000-01-01T06:00:00Z") });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/weather", (route) => route.abort());
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("12:00 AM");
  await expect(scene).toContainText("sunrise over Madison");
  await expect(scene).not.toContainText("students");
  await expect(scene).not.toContainText("class meetings");
  await page.clock.fastForward(17000);
  await expect(scene).toContainText("sunrise over Madison");
});
