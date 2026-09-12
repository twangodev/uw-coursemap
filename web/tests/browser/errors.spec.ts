import { expect, test } from "@playwright/test";

for (const width of [390, 1440]) {
  test(`missing pages preserve HTTP status and offer usable recovery at ${width}px`, async ({
    browser,
  }) => {
    const context = await browser.newContext({
      viewport: { width, height: 900 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const response = await page.goto("/courses/not-a-real-course");
    expect(response?.status()).toBe(404);
    await expect(
      page.getByRole("heading", { name: "A little off course." }),
    ).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
      "content",
      /noindex/,
    );
    await expect(page).toHaveTitle(/404.*uwcourses/);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBe(width);
    await expect(
      page.getByRole("link", { name: "Back home", exact: false }),
    ).toHaveAttribute("href", "/");
    await page
      .getByRole("textbox", { name: "Search courses" })
      .fill("COMPSCI 300");
    await page.getByRole("button", { name: "Search", exact: true }).click();
    await expect(page).toHaveURL(/\/search\?q=COMPSCI(?:\+|%20)300/);
    await expect(
      page.getByRole("link", { name: /Programming II/ }).first(),
    ).toBeVisible();
    await context.close();
  });
}

test("missing page recovery works without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto("/this-page-does-not-exist");
  expect(response?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { name: "A little off course." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Back home", exact: false }).click();
  await expect(page).toHaveURL(/\/$/);
  await context.close();
});
