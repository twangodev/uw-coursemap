import { expect, test } from "@playwright/test";

for (const width of [1440, 390]) {
  test(`expanded disclosures use their container width at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of ["/courses/COMPSCI_300", "/departments/COMPSCI", "/instructors/HOBBES_LEGAULT"]) {
      await page.goto(route);
      await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
      // Opening grade details mounts another set of disclosures; opening evidence
      // loads nested source records. Audit both levels after those updates settle.
      for (let pass = 0; pass < 3; pass++) {
        await page.locator("details").evaluateAll(elements => elements.forEach(element => element.open = true));
        await page.waitForTimeout(350);
      }
      if (route.startsWith("/courses/")) {
        await expect(page.locator(".comparison-method")).toBeVisible();
        await expect(page.locator(".benchmark-note")).toBeVisible();
        await expect(page.locator(".outcomes-table")).toBeVisible();
        await expect(page.getByText("About this estimate", { exact: true })).toBeVisible();
        await page.locator(".comparison-method").screenshot({ path: `test-results/comparison-expanded-${width}.png` });
      } else if (route.startsWith("/departments/")) {
        await expect(page.getByText("About these statistics", { exact: true })).toBeVisible();
      } else {
        await expect(page.locator(".rating-method")).toBeVisible();
      }
      const failures = await page.locator("details p").evaluateAll(elements => elements.flatMap(element => {
        if (!element.getClientRects().length) return [];
        const rect = element.getBoundingClientRect();
        const parent = element.parentElement!;
        const style = getComputedStyle(parent);
        const available = parent.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        const label = element.closest("details")?.querySelector("summary")?.textContent;
        return Math.abs(rect.width - available) > 2 || element.scrollWidth > element.clientWidth + 1
          ? [{ label, width: rect.width, available, text: element.textContent?.slice(0, 80) }] : [];
      }));
      expect(failures, route).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth), route).toBeLessThanOrEqual(width);
    }
  });
}
