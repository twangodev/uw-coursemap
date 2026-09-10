import html from "./viewer.html?raw";

export const prerender = true;

export const GET = () =>
  new Response(html, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
