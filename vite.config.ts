import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";
import { socialImagesDev } from "./web/social-images.mjs";
import { dataAssetsDev } from "./web/data-assets.mjs";
export default defineConfig({
  plugins: [dataAssetsDev(), socialImagesDev(), sveltekit()],
  ssr: { noExternal: ["@lucide/svelte"] },
  server: {
    watch: {
      ignored: ["**/generation/.cache/**", "**/static/data/**", "**/.site/**"],
    },
  },
  test: { include: ["web/tests/**/*.test.ts"] },
});
