<script lang="ts">
  import { MetaTags } from 'svelte-meta-tags';
  import { getLocale, locales, baseLocale, deLocalizeHref, localizeHref } from "$lib/paraglide/runtime";
  import { page } from "$app/state";
  import type { WebSite, WithContext } from "schema-dts";
  import { getOgLocale, getHrefLang } from "$lib/config/languages";
  import * as m from "$lib/paraglide/messages";

  interface Props {
    subtitle?: string;
    description?: string;
    ogImage?: string;
    jsonLd?: any[];
  }

  let {
    subtitle,
    description: customDescription,
    ogImage: customOgImage,
    jsonLd: customJsonLd = []
  }: Props = $props();

  // Site configuration (internationalized)
  const siteName = $derived(m['site.name']());
  const siteDescription = $derived(m['site.description']());
  const siteUrl = "https://uwcourses.com";
  const defaultOgImage = "https://uwcourses.com/uw-coursemap-logo.svg";

  // Get current locale and SEO formats (reactive)
  const currentLocale = $derived(getLocale());
  const currentOgLocale = $derived(getOgLocale(currentLocale));

  // Derive dynamic values
  const title = $derived(subtitle ? `${subtitle} | ${siteName}` : siteName);
  const description = $derived(customDescription || siteDescription);
  const ogImage = $derived(customOgImage || defaultOgImage);

  // Get canonical path (delocalized)
  const canonicalPath = $derived(deLocalizeHref(page.url.pathname + page.url.search));
  const canonicalUrl = $derived(`${siteUrl}${canonicalPath}`);

  // Generate hreflang URLs for all languages
  const languageAlternates = $derived(
    locales.map(locale => ({
      hrefLang: getHrefLang(locale),
      href: locale === baseLocale
        ? `${siteUrl}${canonicalPath}`
        : `${siteUrl}${localizeHref(canonicalPath, { locale })}`
    }))
  );

  // Default structured data for the website
  const websiteSchema = $derived<WithContext<WebSite>>({
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: siteName,
    url: siteUrl,
    description: siteDescription,
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${siteUrl}/explorer?search={search_term_string}`
      },
      query: "required name=search_term_string"
    }
  });

  // Combine structured data
  const jsonLd = $derived([websiteSchema, ...customJsonLd]);
</script>

<MetaTags
  {title}
  {description}
  canonical={canonicalUrl}
  openGraph={{
    url: canonicalUrl,
    title: title,
    description: description,
    images: [{
      url: ogImage,
      alt: siteName
    }],
    siteName: siteName,
    type: 'website',
    locale: currentOgLocale
  }}
  twitter={{
    cardType: 'summary_large_image',
    title: title,
    description: description,
    image: ogImage,
    imageAlt: siteName
  }}
  {languageAlternates}
  additionalMetaTags={[
    {
      name: 'author',
      content: 'UW Course Map'
    },
    {
      name: 'theme-color',
      content: '#c5050c'
    }
  ]}
  additionalRobotsProps={{
    nosnippet: false,
    notranslate: false,
    noimageindex: false,
    noarchive: false,
    maxSnippet: -1,
    maxImagePreview: 'large',
    maxVideoPreview: -1
  }}
/>

<!-- Add hreflang x-default and og:locale:alternate -->
<svelte:head>
  <link rel="alternate" hreflang="x-default" href={`${siteUrl}${canonicalPath}`} />

  <!-- Add og:locale:alternate for other languages -->
  {#each locales.filter(l => l !== currentLocale) as locale}
    <meta property="og:locale:alternate" content={getOgLocale(locale)} />
  {/each}

  <!-- Analytics -->
  <script
    src="https://rybbit.twango.dev/api/script.js"
    data-site-id="1"
    data-track-errors="true"
    data-web-vitals="true"
    defer
  ></script>

  <!-- Structured Data -->
  {@html `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>`}
</svelte:head>