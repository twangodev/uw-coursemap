import { defineConfig } from "vite";
import { resolve } from "node:path";

/** Compile the shared data engine with a local-data adapter, without SvelteKit. */
export default defineConfig({
  esbuild: {
    tsconfigRaw: JSON.stringify({
      compilerOptions: { useDefineForClassFields: true },
    }),
  },
  resolve: {
    alias: [
      {
        find: "$lib/server/runtime",
        replacement: resolve("web/data-context.ts"),
      },
      { find: "$lib", replacement: resolve("src/lib") },
    ],
  },
  build: {
    ssr: "web/generate-data.ts",
    outDir: ".site/compiler",
    emptyOutDir: true,
    rollupOptions: { output: { entryFileNames: "generate-data.mjs" } },
  },
});
