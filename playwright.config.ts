import { defineConfig } from "@playwright/test";
const port = Number(process.env.TEST_PORT || 4173);
const baseURL = `http://127.0.0.1:${port}`;
export default defineConfig({
  testDir: "web/tests/browser",
  use: { baseURL },
  webServer: {
    command: process.env.TEST_PREVIEW
      ? `bun run preview --ip 127.0.0.1 --port ${port}`
      : `bun run dev --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
