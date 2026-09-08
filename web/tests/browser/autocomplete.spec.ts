import { expect, test } from "@playwright/test";

test("course autocomplete supports keyboard selection and dismissal", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const input = page.getByRole("combobox", {
    name: "Search courses or topics",
  });
  await input.fill("CS 300");
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option")
      .first(),
  ).toContainText("300");
  await input.press("Escape");
  await expect(input).toHaveAttribute("aria-expanded", "false");
  await input.fill("CS 400");
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option")
      .first(),
  ).toContainText("400");
  await input.press("ArrowDown");
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option")
      .first(),
  ).toHaveAttribute("aria-selected", "true");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/courses\/cs-400$/);
});

test("finder suggestions retain filters and work on mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/search?subject=COMPSCI&availability=all");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const input = page.getByRole("combobox", {
    name: "Search courses",
    exact: true,
  });
  const request = page.waitForRequest(
    (r) =>
      r.url().includes("/api/search?") &&
      new URL(r.url()).searchParams.get("q") === "300",
  );
  await input.fill("300");
  const url = new URL((await request).url());
  expect(url.searchParams.get("subject")).toBe("COMPSCI");
  expect(url.searchParams.get("availability")).toBe("all");
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option")
      .first(),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("listbox", { name: "Search suggestions" })
    .getByRole("option")
    .first()
    .getByRole("button")
    .click();
  await expect(page).toHaveURL(/\/courses\/cs-300$/);
});

test("autocomplete ignores stale responses and preserves regular search on errors", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.route("**/api/search?**", async (route) => {
    const q = new URL(route.request().url()).searchParams.get("q");
    if (q === "old") await new Promise((resolve) => setTimeout(resolve, 500));
    if (q === "broken")
      return route.fulfill({ status: 503, body: "Unavailable" });
    await route.fulfill({
      json: {
        items: [
          { course_uid: "example", course_id: q, title: "Example course" },
        ],
      },
    });
  });
  const input = page.getByRole("combobox", {
    name: "Search courses or topics",
  });
  const old = page.waitForRequest("**/api/search?*q=old*");
  await input.fill("old");
  await old;
  await input.fill("new");
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option"),
  ).toContainText("new");
  await page.waitForTimeout(600);
  await expect(
    page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("option"),
  ).toContainText("new");
  await input.fill("broken");
  await expect(page.locator(".suggestions")).toContainText(
    "Suggestions unavailable",
  );
  await input.press("Enter");
  await expect(page).toHaveURL(/\/search\?q=broken/);
});

test("autocomplete includes instructors with distinct icons and opens their profiles", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const input = page.getByRole("combobox", {
    name: "Search courses or topics",
  });
  await input.fill("Hobbes");
  const teacher = page
    .getByRole("listbox", { name: "Search suggestions" })
    .getByRole("option")
    .filter({ hasText: "Hobbes Legault" }).filter({ hasText: "current teaching" });
  await expect(teacher).toContainText("Instructor");
  await expect(teacher.locator(".suggestion-icon svg")).toBeVisible();
  await teacher.getByRole("button").click();
  await expect(page).toHaveURL(/\/instructors\//);
  await expect(
    page.getByRole("heading", { name: "Hobbes Legault", exact: true }),
  ).toBeVisible();
});
