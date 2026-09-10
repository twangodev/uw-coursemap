import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";

const date = JSON.parse(readFileSync(".site/campus.json", "utf8")).from;
const now = new Date(`${date}T15:00:00Z`);
async function mockCampus(page: import("@playwright/test").Page) {
  await page.route(`**/campus/**${date}.json`, (route) =>
    route.fulfill({
      json: {
        date,
        buildings: [
          {
            sessions: [
              {
                startsAt: +now - 60000,
                endsAt: +now + 3600000,
                room: "100",
                enrolled: 30,
                courses: [{ code: "COMPSCI 300", section: "LEC 001" }],
                instructors: ["Example Instructor"],
              },
            ],
            name: "Science",
            latitude: 43.075,
            longitude: -89.408,
            events: [
              [+now - 60000, 1, 0],
              [+now + 3600000, 0, 1],
            ],
          },
        ],
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
  await expect(scene).toContainText("students scheduled in class right now");
  await expect(
    scene
      .locator(".fact-value")
      .getByRole("img", { name: "20,350", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".campus-map")).toBeVisible();
  await expect(
    page.locator('.building-heat[data-building="Science"]'),
  ).toHaveAttribute("data-meetings", "1");
  await scene.getByRole("button", { name: "About this campus fact" }).click();
  await expect(page.getByRole("tooltip")).toContainText("not live attendance");
  await page.keyboard.press("Escape");
  await expect(scene.locator(".live-students")).toContainText(
    "students scheduled now",
  );
  await expect(
    scene.getByRole("button", { name: "Next campus fact" }),
  ).toHaveCount(0);
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

test("campus facts rotate with NumberFlow and pause on hover", async ({
  page,
}) => {
  await page.clock.install({ time: now });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await mockCampus(page);
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("students scheduled in class right now");
  const number = await scene.locator(".fact-value").elementHandle();
  await page.clock.fastForward(8500);
  await expect(scene).toContainText("classes in session right now");
  expect(
    await number!.evaluate(
      (el) => el === document.querySelector(".fact-value"),
    ),
  ).toBe(true);
  await scene.locator(".fact-value").hover();
  await page.clock.fastForward(17000);
  await expect(scene).toContainText("classes in session right now");
  await page.mouse.move(0, 0);
  for (let i = 0; i < 3; i++) await page.clock.fastForward(8100);
  await expect(scene.locator(".fact-value .period")).toHaveText("AM");
  await expect(scene.locator(".fact-value .colon")).toHaveText(":");
  await expect(scene.locator(".live-students")).toBeVisible();
});

test("out-of-coverage dates use solar facts without inventing attendance", async ({
  page,
}) => {
  await page.clock.install({ time: new Date("2000-01-01T06:00:00Z") });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/weather", (route) => route.abort());
  await page.goto("/");
  const scene = page.locator(".campus-scene");
  await expect(scene).toContainText("sunrise over Madison");
  await expect(scene).not.toContainText("students");
  await expect(scene).not.toContainText("class meetings");
  await page.clock.fastForward(17000);
  await expect(scene).toContainText("sunrise over Madison");
});

test("building outlines open useful class details by hover, keyboard and tap", async ({
  page,
}) => {
  await page.clock.setFixedTime(now);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockCampus(page);
  await page.goto("/");
  const outline = page.getByRole("button", {
    name: "Science: 1 classes in session",
    exact: true,
  });
  await outline.hover();
  const panel = page.getByRole("region", { name: "Science details" });
  await expect(panel).toBeVisible();
  await expect(
    panel.getByRole("link", { name: "COMPSCI 300" }),
  ).toHaveAttribute("href", "/courses/COMPSCI_300");
  await expect(panel).toContainText("Room 100");
  await expect(panel).toContainText("30 enrolled");
  await expect(panel).toContainText("Example Instructor");
  await page.mouse.move(0, 0);
  await page.keyboard.press("Escape");
  await expect(panel).not.toBeVisible();
  await outline.focus();
  await expect(panel).toBeVisible();
  await panel.getByRole("button", { name: "Close building details" }).click();
  await expect(panel).not.toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await outline.click();
  await expect(panel).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("landing course-search content and SEO are present in server HTML", async ({
  request,
}) => {
  const response = await request.get("/");
  expect(response.status()).toBe(200);
  const html = await response.text();
  expect(html).toContain("Search UW–Madison courses</h1>");
  expect(html).toContain(
    "Compare grades, prerequisites, and professor reviews.",
  );
  expect(html).toContain(
    "Search UW–Madison Courses, Grades &amp; Reviews | uwcourses</title>",
  );
  expect(html).toContain('rel="canonical" href="https://uwcourses.com/"');
  expect(html).toContain('content="index,follow,max-image-preview:large"');
  expect(html).toContain('"@type":"WebSite"');
  expect(html).toContain('href="/departments"');
});
