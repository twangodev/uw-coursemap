import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";
import { socialImagesDev } from "./web/social-images.mjs";
import { sitemapMetadataDev } from "./web/sitemap-metadata.mjs";
export default defineConfig({
  plugins: [socialImagesDev(), sitemapMetadataDev(), sveltekit()],
  ssr: { noExternal: ["@lucide/svelte"] },
  server: {
    watch: { ignored: ["**/generation/.cache/**", "**/static/data/**"] },
  },
  test: { include: ["web/tests/**/*.test.ts"] },
});
