import { expect, test } from "@playwright/test";

test("Madison scene uses local time, schedule assets and optional weather", async ({
  page,
}) => {
  await page.clock.setFixedTime(new Date("2026-09-09T18:00:00Z"));
  await page.route("**/api/weather", (route) =>
    route.fulfill({
      json: {
        available: true,
        temperatureF: 72,
        description: "Fair",
        observedAt: "2026-09-09T17:45:00Z",
        source: "National Weather Service · KMSN",
        sourceUrl: "https://www.weather.gov/wrh/timeseries?site=KMSN",
      },
    }),
  );
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("1:00 PM");
  await expect(scene).toContainText("72°F");
  await expect(scene).toContainText("sessions scheduled now");
  await expect(scene).toContainText("Sunset in");
  await expect(page.getByRole("combobox", { name: "Search courses or topics" })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("scene remains useful when weather is unavailable", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2030-01-01T06:00:00Z"));
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/weather", (route) => route.abort());
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("12:00 AM");
  await expect(scene).toContainText("Madison runs on Central time.");
  await expect(scene).not.toContainText("°F");
  expect(
    await scene
      .locator(".ripples")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
});
