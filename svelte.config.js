import adapter from "@sveltejs/adapter-cloudflare";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { buildSocialImages } from "./web/social-images.mjs";
const cloudflare = adapter({
  // Build/dev loaders use .site/site.sqlite; emulator state need not persist.
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
        await buildSocialImages();
      },
    },
    prerender: {
      concurrency: 16,
      handleHttpError: "fail",
      handleMissingId: "warn",
      entries: ["/sitemap.xml", "/social/manifest.json", "/openapi.json"],
    },
  },
};
