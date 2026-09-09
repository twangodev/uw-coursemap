import { defineConfig } from "@playwright/test";
const preview = Boolean(process.env.TEST_PREVIEW || process.env.CI);
const port = Number(process.env.TEST_PORT || 4173);
const baseURL = `http://127.0.0.1:${port}`;
export default defineConfig({
  testDir: "web/tests/browser",
  // Local workerd serves every browser from one process; avoid saturating it.
  workers: preview ? 2 : undefined,
  globalSetup: preview ? "./web/tests/browser/setup.ts" : undefined,
  use: { baseURL, trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: {
    command: preview
      ? `bun run preview --ip 127.0.0.1 --port ${port} --persist-to .site/browser-state`
      : `bun run dev --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
