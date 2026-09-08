import { test, expect, type Locator } from "@playwright/test";
import { readFile } from "node:fs/promises";
const numberValues = (locator: Locator) => locator.getByRole("img").evaluateAll((nodes) => nodes.map((node) => node.getAttribute("aria-label")));
const uid = "course_28c3390ba944d49fd17f7c72";
test("course reading, citations, graph and theme", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(
    page.getByRole("heading", { name: "Programming II", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Java", { exact: false }).first()).toBeVisible();
  await page.locator("#requirements").scrollIntoViewIfNeeded();
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
  await expect(page.locator(".discovery-card").first()).toContainText(
    "COMPSCI 300",
  );
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByLabel("Search courses", { exact: true }).fill("programming");
  await page.getByRole("button", {name:"Search",exact:true}).click();
  await expect(page.locator(".discovery-card").first()).toBeVisible();
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
    page.getByRole("heading", { name: "Programming II", exact: true }),
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
  const count = grades.locator(".metric-strip");
  const overall = await numberValues(count);
  const instructors = grades.getByRole("button", {
    name: "Instructor",
    exact: true,
  });
  await instructors.click();
  const option = page.getByRole("listbox").getByRole("option").nth(1);
  const response = page.waitForResponse(
    (r) => r.url().includes(`/api/courses/${uid}/grades`) && r.ok(),
  );
  await option.click();
  await response;
  await expect(grades.getByText("Loading grades…")).not.toBeVisible();
  await instructors.click();
  await page.getByRole("option", { name: "Course overall", exact: true }).click();
  await expect.poll(() => numberValues(count)).toEqual(overall);
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
    page.getByRole("heading", { name: /on the Hill/ }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/home.png", fullPage: true });
  await page.goto("/courses/course_63e805b33518ff3fd8dc0a39");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(page.locator("h1")).toContainText("High Performance Computing");
  await page.locator("#grades").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "test-results/cs759.png", fullPage: true });
});

test("calendar filters meetings, exposes details and exports dates", async ({
  page,
}) => {
  await page.goto(`/courses/${uid}`);
  const schedule = page.locator("#schedule");
  await schedule.scrollIntoViewIfNeeded();
  await expect(schedule.locator(".week-grid")).toBeVisible();
  await page.getByLabel("Calendar section").selectOption("LEC 001");
  await expect(schedule.locator(".meeting").first()).toContainText("LEC 001");
  await expect(
    schedule.locator(".meeting").filter({ hasText: "LEC 002" }),
  ).toHaveCount(0);
  await schedule.locator(".meeting").first().click();
  await expect(
    page.getByRole("region", { name: "Meeting details" }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export", exact: true }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe("course-schedule.ics");
  const exported = await readFile((await file.path())!, "utf8");
  expect(exported).toContain("BEGIN:VCALENDAR");
  expect(exported).toContain("SUMMARY:COMPSCI 300 · LEC 001");
  expect(exported).not.toContain("SUMMARY:COMPSCI 300 · LEC 002");
  expect(exported).toContain("DTSTART:20260907T145500Z");
  await page.getByRole("button", { name: "Next week" }).click();
  await expect(schedule.locator(".week-label")).toContainText("Sep 14");
  await expect(page.getByRole("tab")).toHaveCount(0);
  await page.screenshot({ path: "test-results/calendar-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(schedule.locator(".agenda")).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({ path: "test-results/calendar-mobile.png" });
});

test("course context, projection and captured instructor ratings remain distinct", async ({
  page,
}) => {
  await page.goto(`/courses/${uid}`);
  await expect(
    page.locator(".grade-snapshot .grade-percentages"),
  ).toContainText("34.1%");
  await expect(page.getByRole("button", { name: "Term", exact: true })).toContainText("Fall 2026");
  await expect(page.locator("#grades .grade-estimate")).toContainText("Fall 2026");
  await expect(page.locator("#grades .grade-estimate")).toContainText("prediction interval");
  await expect(page.locator(".projection")).toHaveCount(0);
  await page.locator("#grades").screenshot({ path: "/tmp/uw-coursemap-design-audit/projected-grades.png" });
  const hobbes = page
    .locator("#professors article")
    .filter({ hasText: "Hobbes Legault" });
  await expect(hobbes.locator(".rating-values").getByRole("img", { name: "93", exact: true })).toBeVisible();
  await expect(hobbes.locator(".rating-values")).toContainText("RMP quality");
  await hobbes.getByRole("link", { name: "Hobbes Legault" }).click();
  await expect(
    page.getByRole("heading", { name: "Hobbes Legault", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".rating-values").getByRole("img", { name: "93", exact: true })).toBeVisible();
});

test("takeaways rotate and pause for reading sources", async ({ page }) => {
  await page.clock.install();
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const card = page.getByRole("region", { name: "Student takeaways", exact: true });
  const initial = await card.locator(".claim > p").textContent();
  await page.mouse.move(0, 0);
  await page.clock.fastForward(8000);
  await expect(card.locator(".claim > p")).not.toHaveText(initial!);
  await card.getByRole("button", { name: "Pause takeaway rotation" }).click();
  const paused = await card.locator(".claim > p").textContent();
  await page.mouse.move(0, 0);
  await page.clock.fastForward(16000);
  await expect(card.locator(".claim > p")).toHaveText(paused!);
  await card.getByRole("button", { name: "Next takeaway" }).click();
  await expect(card.locator(".claim > p")).not.toHaveText(paused!);
  await card.locator("[data-citation-trigger]").first().click();
  await expect(page.getByRole("dialog", { name: "Sources", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close sources", exact: true }).click();
  await card.getByRole("button", { name: "Resume takeaway rotation" }).click();
  await card.locator("[data-citation-trigger]").first().click();
  const reading = await card.locator(".claim > p").textContent();
  await page.mouse.move(0, 0);
  await page.clock.fastForward(16000);
  await expect(card.locator(".claim > p")).toHaveText(reading!);
});

test("school and department comparisons stay synchronized", async ({ page }) => {
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "Spring 2026", exact: true }).click();
  const metrics = page.locator("#grades .metric-strip");
  await expect(page.getByRole("tooltip")).toHaveCount(0);
  const trigger = metrics.getByRole("button", { name: "Average GPA comparison", exact: true });
  await trigger.hover();
  await expect(page.getByRole("tooltip")).toBeVisible();
  const school = await numberValues(page.getByRole("tooltip"));
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Comparison group", exact: true }).click();
  await page.getByRole("option", { name: "Department · COMPSCI", exact: true }).click();
  await trigger.focus();
  await expect(page.getByRole("tooltip")).toContainText("COMPSCI");
  await expect.poll(() => numberValues(page.getByRole("tooltip"))).not.toEqual(school);
  await page.keyboard.press("Escape");
  await expect(page.locator(".course-context .context-heading")).toContainText("COMPSCI");
  await expect(metrics.locator(".metric-tooltip-trigger")).toHaveCount(3);
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "Spring 2026", exact: true }).click();
  await expect(metrics.getByRole("img", { name: "478", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Comparison group", exact: true }).click();
  await page.keyboard.press("Home");
  await page.keyboard.press("Enter");
  await expect(page.locator(".course-context .context-heading")).toContainText("UW–Madison");
});

test("animated numbers preserve accessible values with reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const metrics = page.locator("#grades .metric-strip");
  await expect(page.locator(".grade-snapshot").getByRole("img", { name: "11,038", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "Spring 2026", exact: true }).click();
  await expect(metrics.getByRole("img", { name: "478", exact: true })).toBeVisible();
  expect(await metrics.locator("number-flow-svelte").evaluateAll((nodes) => nodes.every((node) => !node.shadowRoot?.getAnimations().some((animation) => animation.playState === "running")))).toBe(true);
});

test("metric comparison details open on touch", async ({ browser }) => {
  const context = await browser.newContext({ hasTouch: true, viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:4173/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.locator(".grade-snapshot").getByRole("button", { name: "Average GPA comparison" }).tap();
  await expect(page.getByRole("tooltip")).toContainText("UW–Madison");
  await page.locator("h1").tap();
  await expect(page.getByRole("tooltip")).toHaveCount(0);
  await context.close();
});

test("inline citations show original comments without expanding the page", async ({ page }) => {
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const trigger = page.locator("#overview [data-citation-trigger]").first();
  const before = await page.locator("#overview").boundingBox();
  await trigger.click();
  const sources = page.getByRole("dialog", { name: "Sources", exact: true });
  await expect(sources.locator("blockquote").first()).toBeVisible();
  await expect(sources).toContainText("Rate My Professors");
  await expect(sources.getByRole("link", { name: "View RMP profile" }).first()).toHaveAttribute("href", /^https:\/\/www.ratemyprofessors.com\/professor\//);
  expect((await page.locator("#overview").boundingBox())?.height).toBe(before?.height);
  await expect(sources.locator("pre")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(sources).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("grade history fits curved instructor lines and identifies them on hover", async ({ page }) => {

  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const chart = page.locator("#grades .charts > div").last();
  const paths = chart.locator("path.lc-path");
  expect(await paths.evaluateAll((nodes) => nodes.filter((node) => node.getAttribute("d")?.includes("C")).length)).toBeGreaterThan(4);
  await expect(chart.locator(".trend-legend")).toHaveCount(0);
  await chart.locator(".chart").hover();
  await expect(page.locator(".lc-tooltip-root")).toContainText("Course average");
  await expect(page.locator(".lc-tooltip-root")).not.toContainText("total");
  await chart.screenshot({ path: "/tmp/uw-coursemap-design-audit/all-instructor-trends.png" });
});

test("term selection updates context, roster, history and snapshot availability", async ({ page }) => {
  await page.goto(`/courses/${uid}`);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.locator(".course-facts").screenshot({ path: "/tmp/uw-coursemap-design-audit/course-details-spaced.png" });
  const term = page.getByRole("button", { name: "Term", exact: true });
  await expect(term).toContainText("Fall 2026");
  const rosterCount = await page.locator("#professors .professor-tile").count();
  await expect(page.locator('.current-teachers a[href^="/instructors/"]')).toHaveCount(Math.min(rosterCount, 3));
  if (rosterCount > 3) await expect(page.locator('.current-teachers a[href="#professors"]')).toContainText(`+${rosterCount - 3} more`);
  const allTimeGrades = await numberValues(page.locator(".grade-snapshot"));
  await term.click();
  await page.getByRole("option", { name: "Spring 2026", exact: true }).click();
  await expect(page.locator(".course-context")).toContainText("Spring 2026");
  await expect(page.locator(".course-context").getByRole("img", { name: "478", exact: true })).toBeVisible();
  await expect(page.locator("#professors .panel-heading")).toContainText("Spring 2026");
  await expect(page.locator("#professors")).not.toContainText("Ben Jacobsen");
  await expect(page.locator("#professors .teaching-grades").first()).toContainText("Spring 2026");
  await expect(page.locator("#overview [data-citation-trigger]").first()).toBeVisible();
  expect(await numberValues(page.locator(".grade-snapshot"))).toEqual(allTimeGrades);
  await expect(page.locator("#experience")).toContainText("No student-experience summary for Spring 2026");
  await expect(page.locator("#requirements")).toContainText("No prerequisite snapshot for Spring 2026");
  await expect(page.locator("#schedule")).toContainText("No calendar captured for Spring 2026");
  await expect(page.locator("#schedule tbody tr")).toHaveCount(0);
  await expect(page.locator("#grades .grade-estimate")).toHaveCount(0);
  await expect(page.locator("#grades")).toContainText("through Spring 2026");
  await page.getByRole("button", { name: "Comparison group", exact: true }).click();
  await page.getByRole("option", { name: "Department · COMPSCI", exact: true }).click();
  await page.locator("#professors .teaching-grades").first().getByRole("button").focus();
  await expect(page.getByRole("tooltip")).toContainText("COMPSCI");
  await page.keyboard.press("Escape");
  await term.click();
  await page.getByRole("option", { name: "Fall 2026 · Projected", exact: true }).click();
  await expect(page.locator("#professors")).toContainText("Ben Jacobsen");
  await expect(page.locator("#grades")).toContainText("Fall 2026 · Projected");
  await expect(page.locator("#grades .metric-strip")).toHaveCount(0);
  await expect(page.locator("#grades .grade-estimate")).toBeVisible();
  await expect(page.locator("#overview [data-citation-trigger]").first()).toBeVisible();
  await expect(page.locator("#schedule tbody tr").first()).toBeVisible();
});

test("historical instructors without a recorded name do not break course pages", async ({ page }) => {
  const response = await page.goto("/courses/course_f55fac894a94d4843c58c348");
  expect(response?.status()).toBe(200);
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "All recorded terms", exact: true }).click();
  await expect(page.locator("#professors")).toContainText("Unknown instructor");
});

test("insufficient projection history falls back only inside grades", async ({ page }) => {
  await page.goto("/courses/course_c7911cf4ed9adf4f70e4ddcd");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await expect(page.getByRole("button", { name: "Term", exact: true })).toHaveText("Fall 2026");
  await expect(page.locator("#grades .fallback-note")).toContainText("Latest available · Spring 2022");
  await expect(page.locator("#grades .grade-estimate")).toHaveCount(0);
  await expect(page.locator("#grades .metric-strip")).toBeVisible();
  await expect(page.locator("#professors .panel-heading")).toContainText("Fall 2026");
  await page.getByRole("button", { name: "Term", exact: true }).click();
  await page.getByRole("option", { name: "Spring 2022", exact: true }).click();
  await expect(page.locator("#grades .fallback-note")).toHaveCount(0);
  await expect(page.locator("#grades .grade-percentages")).toBeVisible();
});
