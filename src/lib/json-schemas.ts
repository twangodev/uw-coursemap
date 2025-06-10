import type { Organization, WithContext } from "schema-dts";

export const university: WithContext<Organization> = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "University of Wisconsin-Madison",
  alternateName: "UW-Madison",
  url: "https://www.wisc.edu",
};
