import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig(({ mode }) => {
  return {
    plugins: [sveltekit()],
    ssr: {
      noExternal: mode === "production" ? ["@carbon/charts"] : [],
    },
    server: {
      watch: {
        ignored: [
            "**/data/**"
        ]
      }
    }
  };
});
