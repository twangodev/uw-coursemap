import { test, expect } from '@playwright/test';

test('floating surfaces use short entrance and exit motion', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.goto('/courses/COMPSCI_300');
  await expect(page.locator('html')).toHaveAttribute('data-hydrated', 'true');
  await page.getByRole('button', { name: 'Comparison group', exact: true }).click();
  const menu = page.locator('.course-select-content');
  await expect(menu).toBeVisible();
  expect(await menu.evaluate(e => getComputedStyle(e).animationName)).toBe('surface-arrive');
  expect(await menu.evaluate(e => getComputedStyle(e).animationDuration)).toBe('0.18s');
  await page.keyboard.press('Escape');
  await expect(menu).toHaveCount(0);
  await page.locator('.course-identity .evidence-badge').first().hover();
  const popup = page.locator('.badge-evidence');
  await expect(popup).toBeVisible();
  expect(await popup.evaluate(e => getComputedStyle(e).animationName)).toBe('surface-arrive');
  await page.keyboard.press('Escape');
  await expect(popup).toHaveCount(0);
});

test('text disclosures finish expansion and collapse without clipping content', async ({ page }) => {
  await page.goto('/courses/COMPSCI_300');
  await expect(page.locator('html')).toHaveAttribute('data-hydrated', 'true');
  const details = page.locator('.comparison-method');
  await details.locator('summary').click();
  await expect(details.locator('p').last()).toBeVisible();
  await expect.poll(() => details.evaluate(e => {
    const content = getComputedStyle(e, '::details-content');
    return parseFloat(content.height) > 30 && content.opacity === '1';
  })).toBe(true);
  await details.locator('summary').click();
  await expect.poll(() => details.evaluate(e => getComputedStyle(e, '::details-content').height)).toBe('0px');
  await details.locator('summary').click();
  await expect(details.locator('p').last()).toBeVisible();
});

test('reduced motion disables movement and automatic takeaway rotation', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/courses/COMPSCI_300');
  await expect(page.getByRole('button', { name: 'Resume takeaway rotation' })).toBeVisible();
  await page.locator('.course-identity .evidence-badge').first().click();
  const popup = page.locator('.badge-evidence');
  await expect(popup).toBeVisible();
  expect(await popup.evaluate(e => getComputedStyle(e).animationName)).toBe('none');
  expect(await page.locator('.section-indicator').evaluate(e => getComputedStyle(e).transitionDuration)).toBe('0s');
  await page.keyboard.press('Escape');
  await page.locator('.comparison-method summary').click();
  await expect(page.locator('.comparison-method p').last()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
