import { paraglideVitePlugin } from "@inlang/paraglide-js";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import devtoolsJson from "vite-plugin-devtools-json";

export default defineConfig(({ mode }) => {
  return {
    plugins: [
      sveltekit(),
      devtoolsJson(),
      paraglideVitePlugin({
        project: "./project.inlang",
        outdir: "./src/lib/paraglide",
        strategy: ["url", "cookie", "preferredLanguage", "baseLocale"], // URL → saved preference → browser language → English
      }),
    ],
    ssr: {
      noExternal: mode === "production" ? ["@carbon/charts"] : [],
    },
    server: { watch: { ignored: ["**/data/**"] } },
  };
});
