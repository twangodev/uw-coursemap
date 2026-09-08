import adapter from "@sveltejs/adapter-cloudflare";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      config: process.env.WRANGLER_CONFIG || "wrangler.jsonc",
    }),
    prerender: {
      concurrency: 16,
      handleHttpError: "fail",
      handleMissingId: "warn",
      entries: ["/", "/subjects", "/departments", "/explorer", "/stats"],
    },
  },
};
