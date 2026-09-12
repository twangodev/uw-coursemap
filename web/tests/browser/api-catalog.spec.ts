import { expect, test } from "@playwright/test";

test("API catalog exposes the specification and documentation", async ({
  request,
}) => {
  const response = await request.get("/.well-known/api-catalog", {
    headers: { Accept: "application/linkset+json" },
  });
  expect(response.status()).toBe(200);
  expect(response.headers()).toMatchObject({
    "content-type":
      'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"',
    "cache-control": "public, max-age=3600",
    "access-control-allow-origin": "*",
    link: '<https://uwcourses.com/.well-known/api-catalog>; rel="api-catalog"',
  });
  const catalog = await response.json();
  expect(catalog.linkset).toHaveLength(1);
  const api = catalog.linkset[0];
  expect(api.anchor).toBe("https://uwcourses.com");
  expect(api["service-desc"][0]).toMatchObject({
    href: "https://uwcourses.com/openapi.json",
    type: "application/vnd.oai.openapi+json",
  });
  expect(api["service-doc"][0]).toMatchObject({
    href: "https://uwcourses.com/openapi",
    type: "text/html",
  });
  const spec = await request.get(new URL(api["service-desc"][0].href).pathname);
  expect(spec.status()).toBe(200);
  expect((await spec.json()).openapi).toBe("3.1.0");
  const docs = await request.get(new URL(api["service-doc"][0].href).pathname);
  expect(docs.status()).toBe(200);
  expect(await docs.text()).toContain('id="openapi-viewer"');

  const head = await request.head("/.well-known/api-catalog");
  expect(head.status()).toBe(200);
  for (const name of [
    "content-type",
    "cache-control",
    "access-control-allow-origin",
    "link",
  ])
    expect(head.headers()[name]).toBe(response.headers()[name]);
  expect(await head.body()).toHaveLength(0);
});

test("pages advertise API discovery before JavaScript runs", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/");
  const link = page.locator('head link[rel="api-catalog"]');
  await expect(link).toHaveCount(1);
  await expect(link).toHaveAttribute(
    "href",
    "https://uwcourses.com/.well-known/api-catalog",
  );
  await expect(link).toHaveAttribute("type", "application/linkset+json");
  await context.close();
});
