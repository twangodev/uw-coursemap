const headers = {
  "Content-Type":
    'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"',
  "Cache-Control": "public, max-age=3600",
  "Access-Control-Allow-Origin": "*",
  Link: '<https://uwcourses.com/.well-known/api-catalog>; rel="api-catalog"',
};

const catalog = {
  linkset: [
    {
      anchor: "https://uwcourses.com",
      "service-desc": [
        {
          href: "https://uwcourses.com/openapi.json",
          type: "application/vnd.oai.openapi+json",
          title: "uwcourses public API",
        },
      ],
      "service-doc": [
        {
          href: "https://uwcourses.com/openapi",
          type: "text/html",
          title: "API documentation and usage",
        },
      ],
    },
  ],
};

export const GET = () => new Response(JSON.stringify(catalog), { headers });

export const HEAD = () => new Response(null, { headers });
