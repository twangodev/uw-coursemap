import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";
export default defineConfig({
  plugins: [sveltekit()],
  ssr: { noExternal: ["@lucide/svelte"] },
  server: {
    watch: { ignored: ["**/generation/.cache/**", "**/static/data/**"] },
  },
  test: { include: ["web/tests/**/*.test.ts"] },
});
