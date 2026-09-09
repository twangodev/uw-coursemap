import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";
import { socialImagesDev } from "./web/social-images.mjs";
export default defineConfig({
  plugins: [socialImagesDev(), sveltekit()],
  ssr: { noExternal: ["@lucide/svelte"] },
  server: {
    watch: { ignored: ["**/generation/.cache/**", "**/static/data/**"] },
  },
  test: { include: ["web/tests/**/*.test.ts"] },
});
