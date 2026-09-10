import { cp, mkdir, rm, rename } from "node:fs/promises";
import { buildSocialImages } from "./social-images.mjs";
const staging = ".site/social.tmp";
await rm(staging, { recursive: true, force: true });
await mkdir(`${staging}/social`, { recursive: true });
await cp(
  ".site/documents/social/manifest.json",
  `${staging}/social/manifest.json`,
);
await cp(".site/documents/.release.json", `${staging}/.release.json`);
await buildSocialImages(staging);
await rm(".site/social", { recursive: true, force: true });
await rename(staging, ".site/social");
