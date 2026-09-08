import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "web/tests/browser",
  use: { baseURL: "http://127.0.0.1:4173" },
  webServer: {
    command: "bun run dev --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
