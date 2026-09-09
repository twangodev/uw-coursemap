import { expect, test } from '@playwright/test';

test('course badges explain scope and respond to term and comparison changes', async ({ page }) => {
  await page.goto('/courses/COMPSCI_300');
  await expect(page.locator('html')).toHaveAttribute('data-hydrated', 'true');
  const header = page.locator('.course-identity');
  await expect(header.locator('.evidence-badge')).toHaveCount(3);
  await header.getByRole('button', { name: 'Highly rated instructor', exact: true }).hover();
  const evidence = page.getByRole('dialog', { name: 'Highly rated instructor evidence' });
  await expect(evidence).toContainText('Hobbes Legault');
  await expect(evidence).toContainText('Fall 2026');
  expect(await header.getByRole('button', { name: 'Highly rated instructor', exact: true }).evaluate(e => e.matches(':focus-visible'))).toBe(false);
  await page.keyboard.press('Escape');
  await expect(evidence).toHaveCount(0);
  await header.getByRole('button', { name: 'Lower grades', exact: true }).focus();
  await expect(page.getByRole('dialog', { name: 'Lower grades evidence' })).toContainText('Spring 2026');
  await page.keyboard.press('Escape');
  await expect(page.locator('.badge-evidence')).toHaveCount(0);
  await page.getByRole('button', { name: 'Comparison group', exact: true }).click();
  await page.getByRole('option', { name: 'Department · COMPSCI', exact: true }).click();
  const grades = header.locator('.evidence-badge').filter({ hasText: /Higher grades|Lower grades/ });
  if (await grades.count()) {
    await grades.press('Tab');
    await grades.focus();
    await expect(page.locator('.badge-evidence')).toContainText('Computer Sciences');
    await page.keyboard.press('Escape');
  }
  await page.getByRole('button', { name: 'Term', exact: true }).click();
  await page.getByRole('option', { name: 'All recorded terms', exact: true }).click();
  await page.keyboard.press('Tab');
  await header.getByRole('button', { name: 'Highly rated instructor', exact: true }).focus();
  await expect(page.locator('.badge-evidence')).toContainText('Fall 2026');
});

test('profiles and discovery lists share badges without nesting buttons in links', async ({ page }) => {
  for (const route of ['/instructors/HOBBES_LEGAULT', '/instructors/by-rating-count', '/search?q=CS300', '/departments/COMPSCI']) {
    await page.goto(route);
    await expect(page.locator('.evidence-badge').first()).toBeVisible();
    await expect(page.locator('a .evidence-badge')).toHaveCount(0);
    expect(await page.locator('.discovery-card .student-badges, .instructor-result .student-badges').evaluateAll(rows => rows.every(row => row.children.length <= 2))).toBe(true);
  }
});

test('badge evidence opens on touch and fits mobile and dark layouts', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  await page.goto(new URL('/courses/COMPSCI_300', baseURL).href);
  await expect(page.locator('html')).toHaveAttribute('data-hydrated', 'true');
  await page.locator('.course-identity').getByRole('button', { name: 'Highly rated instructor', exact: true }).tap();
  const evidence = page.getByRole('dialog', { name: 'Highly rated instructor evidence' });
  await expect(evidence).toBeVisible();
  await expect.poll(() => evidence.evaluate(e => { const r = e.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; })).toBe(true);
  await page.getByRole('button', { name: 'Close badge evidence' }).tap();
  await expect(evidence).toHaveCount(0);
  await page.getByLabel('Color theme').selectOption('dark');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: 'test-results/badges-mobile-dark.png' });
  await context.close();
});

test('AI suggestion info names the exact recorded model with its family logo', async ({ page }) => {
  await page.goto('/courses/COMPSCI_300');
  const info = page.getByRole('button', { name: 'About AI suggestions' });
  await info.hover();
  const tooltip = page.getByRole('tooltip').filter({ hasText: 'nvidia/Qwen3.6-35B-A3B-NVFP4' });
  await expect(tooltip).toBeVisible();
  await expect(tooltip).toContainText('1355db6a052410cfd62085d94b58866fd0f2c3c5');
  await expect(tooltip.getByRole('img', { name: 'Qwen' })).toBeVisible();
  expect(await tooltip.getByRole('img', { name: 'Qwen' }).evaluate(e => getComputedStyle(e).maskImage)).not.toBe('none');
  await expect(page.getByText('AI suggested', { exact: true })).toHaveCount(0);
  await page.screenshot({ path: 'test-results/ai-info.png', animations: 'disabled' });
});
