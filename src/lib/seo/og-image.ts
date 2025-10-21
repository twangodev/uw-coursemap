/**
 * Utilities for generating Open Graph images using ogis.dev
 */

const OG_IMAGE_BASE_URL = "https://img.ogis.dev/";
const DEFAULT_LOGO = "https://docs.uwcourses.com/assets/uw-coursemap-light.png";
const DEFAULT_TEMPLATE = "daybreak";

export interface OgImageOptions {
  title: string;
  subtitle?: string;
  description: string;
  logo?: string;
  template?: string;
}

/**
 * Generate an Open Graph image URL using ogis.dev
 */
export function generateOgImageUrl(options: OgImageOptions): string {
  const params = new URLSearchParams({
    title: options.title,
    description: options.description,
    logo: options.logo || DEFAULT_LOGO,
    template: options.template || DEFAULT_TEMPLATE,
  });

  if (options.subtitle) {
    params.set('subtitle', options.subtitle);
  }

  return `${OG_IMAGE_BASE_URL}?${params.toString()}`;
}

/**
 * Generate the default OG image for the home page
 */
export function generateDefaultOgImage(): string {
  return generateOgImageUrl({
    title: "uwcourses.com",
    description: "Explore the courses offered by UW-Madison in a visual and interactive way.",
  });
}
