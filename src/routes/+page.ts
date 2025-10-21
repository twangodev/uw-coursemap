import { generateDefaultOgImage } from "$lib/seo/og-image";

export const load = async () => {
  const ogImage = generateDefaultOgImage();

  return {
    ogImage: ogImage,
  };
};
