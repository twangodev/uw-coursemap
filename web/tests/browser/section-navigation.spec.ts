import { test, expect } from '@playwright/test';

for (const width of [1440, 390]) test(`section indicator follows scrolling at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/courses/COMPSCI_300');
  await expect(page.locator('html')).toHaveAttribute('data-hydrated', 'true');
  const nav = page.getByRole('navigation', { name: 'Course sections' });
  await expect(nav.locator('.section-indicator')).toHaveCount(1);
  for (const id of ['requirements', 'professors', 'grades', 'overview']) {
    await page.locator(`#${id}`).evaluate(el => window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 100, behavior: 'instant' }));
    const link = nav.locator(`a[href="#${id}"]`);
    await expect(link).toHaveAttribute('aria-current', 'location');
    await expect.poll(() => nav.evaluate(el => {
      const indicator = el.querySelector('.section-indicator')!.getBoundingClientRect();
      const active = el.querySelector('[aria-current="location"]')!.getBoundingClientRect();
      return Math.abs(indicator.left - active.left) < 1 && Math.abs(indicator.width - active.width) < 1;
    })).toBe(true);
    await expect.poll(() => link.evaluate(el => {
      const r = el.getBoundingClientRect(); const n = el.closest('nav')!.getBoundingClientRect();
      return r.left >= n.left - 1 && r.right <= n.right + 1;
    })).toBe(true);
  }
  await nav.getByRole('link', { name: 'prerequisites' }).click();
  await expect(nav.getByRole('link', { name: 'prerequisites' })).toHaveAttribute('aria-current', 'location');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await nav.locator('.section-indicator').evaluate(el => getComputedStyle(el).transitionDuration)).toBe('0s');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
});
