import { expect, test } from "@playwright/test";
test("course history charts expand on demand for an ungraded current term", async ({
  page,
}) => {
  await page.goto("/courses/COMPSCI_300");
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  const history = page.getByRole("region", {
    name: "Historical grade outcomes",
  });
  await expect(history).toHaveCount(0);
  await page.locator(".more-grade-details > summary").click();
  await history.scrollIntoViewIfNeeded();
  await expect(
    history.getByRole("heading", { name: "Grade mix over time" }),
  ).toBeVisible();
  await expect(
    history.getByRole("heading", { name: "Recorded grades by term" }),
  ).toBeVisible();
  await expect(history.locator("svg").first()).toBeVisible();
  await page
    .getByText("Grade counts & non-letter outcomes", { exact: true })
    .click();
  await expect(page.locator(".outcomes-table")).toContainText("Spring 2026");
  await page.locator(".more-grade-details > summary").click();
  await expect(history).toHaveCount(0);
});
test("departments and prerequisite maps serve distinct purposes", async ({
  page,
}) => {
  await page.goto("/departments/COMPSCI");
  await expect(
    page.getByRole("heading", { name: "Computer Sciences", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Explore prerequisite map" }).click();
  await expect(page).toHaveURL(/explorer\/COMPSCI$/);
  await expect(
    page.getByRole("heading", { name: "Computer Sciences prerequisite map" }),
  ).toBeVisible();
  await expect(page.locator(".svelte-flow__node").first()).toBeVisible();
  await page.getByLabel("Find a course on the map").fill("COMPSCI 400");
  await page.getByRole("button", { name: "COMPSCI 400", exact: true }).click();
  await expect(page.locator(".map-node.focused")).toContainText("COMPSCI 400");
  await page
    .getByRole("link", { name: "Department courses & statistics" })
    .click();
  await expect(page).toHaveURL(/departments\/COMPSCI$/);
});
