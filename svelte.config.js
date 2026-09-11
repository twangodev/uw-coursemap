import adapter from "@sveltejs/adapter-cloudflare";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { assembleAssets } from "./web/assemble-assets.mjs";
const cloudflare = adapter({
  // Build/dev loaders use .site/import/site.sqlite; emulator state need not persist.
  platformProxy: { persist: false },
  config: process.env.WRANGLER_CONFIG || "wrangler.json",
});
export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: {
      ...cloudflare,
      async adapt(builder) {
        await cloudflare.adapt(builder);
        // CI compiles in parallel with data preparation, then assembles before auditing.
        if (process.env.SITE_ASSETS !== "deferred") await assembleAssets();
      },
    },
    prerender: {
      concurrency: 4,
      handleHttpError: "fail",
      handleMissingId: "warn",
      entries: ["*", "/openapi.json"],
    },
  },
};
