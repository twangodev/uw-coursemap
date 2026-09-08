<script lang="ts">
  import { onMount } from "svelte";
  import { ArrowLeft, ArrowUpRight, Search, X, Info } from "@lucide/svelte";
  import { courseUrl, normalize, courseTitle } from "$lib/format";
  import { departmentName } from "$lib/departments";
  import type { CourseMapData } from "$lib/course-map";
  let { data }: { data: { subject: string | null; graph: CourseMapData } } = $props();
  let Graph = $state<any>(null);
  let query = $state("");
  let chosen = $state("");
  let loadError = $state(false);
  let candidates = $derived(query.trim() ? data.graph.courses.filter(course =>
    normalize(`${course.code} ${course.title}`).includes(normalize(query)),
  ).sort((a, b) => Number(normalize(b.code) === normalize(query)) - Number(normalize(a.code) === normalize(query)) || a.code.localeCompare(b.code)).slice(0, 8) : []);
  let selected = $derived(data.graph.courses.find(course => course.uid === chosen));
  let incoming = $derived(data.graph.edges.filter(edge => edge.target === chosen).length);
  let outgoing = $derived(data.graph.edges.filter(edge => edge.source === chosen).length);
  let title = $derived(data.subject ? `${departmentName(data.subject)} prerequisite map` : "Course prerequisite map");
  function select(uid: string) { chosen = uid; query = ""; }
  onMount(() => {
    const requested = new URL(location.href).searchParams.get("course");
    if (requested) chosen = data.graph.courses.find(course => normalize(course.code) === normalize(requested))?.uid || "";
    import("./CourseMap.svelte").then(module => Graph = module.default).catch(() => loadError = true);
  });
</script>

<svelte:head>
  <title>{title} · UW Courses</title>
  <meta name="description" content={`Explore course prerequisite relationships${data.subject ? ` in ${departmentName(data.subject)}` : " at UW–Madison"}.`} />
</svelte:head>

<div class="explorer">
  {#if Graph}<Graph data={data.graph} focus={chosen} onSelect={select} />{:else}<p class="loading" role="status">{loadError ? "Unable to load the map. Reload to try again." : "Loading prerequisite map…"}</p>{/if}
  <div class="map-toolbar">
    <div class="map-heading">
      <a class="back" href={data.subject ? `/departments/${encodeURIComponent(data.subject)}` : "/departments"} aria-label="Department courses & statistics"><ArrowLeft size={17} /></a>
      <a class="map-brand" href="/" aria-label="UW Courses home"><img src="/uw-coursemap-logo.svg" alt="" width="24" height="24" /></a>
      <div><h1>{title}</h1><p>{data.graph.courses.length.toLocaleString()} courses · {data.graph.edges.length.toLocaleString()} connections</p></div>
    </div>
    <div class="map-search">
      <Search size={16} />
      <input aria-label="Find a course on the map" type="search" placeholder="Find a course…" bind:value={query} onkeydown={event => { if (event.key === "Escape") query = ""; if (event.key === "Enter" && candidates[0]) select(candidates[0].uid); }} />
    </div>
    {#if query.trim()}<div class="map-results" aria-label="Matching courses">
      {#each candidates as course}<button onclick={() => select(course.uid)} aria-label={course.code}><strong>{course.code}</strong><span>{courseTitle(course.title)}</span></button>{:else}<p>No matching courses.</p>{/each}
    </div>{/if}
  </div>
  {#if selected}<aside class="selected-course" aria-label="Selected course">
    <div class="selection-heading"><span>{selected.code}</span><button aria-label="Clear selected course" onclick={() => select("")}><X size={16} /></button></div>
    <h2>{courseTitle(selected.title)}</h2>
    <p>{incoming} prerequisite references · {outgoing} following courses</p>
    <a href={courseUrl(selected.code)}>Open course <ArrowUpRight size={15} /></a>
  </aside>{/if}
  <details class="map-help"><summary aria-label="About this map"><Info size={17} /></summary><p>Drag to pan; scroll or pinch to zoom. Select a course to highlight its connections. Arrows point from a prerequisite reference to the course that mentions it. Alternatives are included; open the course for complete requirements and exclusions.</p></details>
</div>

<style>
  .explorer { position: relative; width: 100%; height: 100dvh; overflow: hidden; }
  .loading { position: absolute; inset: 50% 0 auto; text-align: center; color: var(--muted); }
  .map-toolbar { position: absolute; top: 20px; left: 20px; width: min(420px, calc(100% - 40px)); border: 1px solid var(--border); border-radius: 7px; background: var(--bg); box-shadow: 0 3px 18px #00000008; }
  .map-heading { display: flex; align-items: center; gap: 12px; padding: 16px; }
  .back { display: grid; place-items: center; color: var(--muted); }
  .map-brand { display: flex; flex-shrink: 0; }
  h1 { font-size: 16px; line-height: 1.25; font-weight: 550; letter-spacing: -0.02em; margin: 0; }
  .map-heading p { margin: 5px 0 0; font-size: 12px; color: var(--muted); }
  .map-search { display: flex; align-items: center; gap: 10px; padding: 0 16px; border-top: 1px solid var(--border); color: var(--muted); }
  input { min-width: 0; width: 100%; border: 0; border-radius: 0; padding: 12px 0; background: transparent; font-size: 14px; }
  .map-results { border-top: 1px solid var(--border); padding: 6px; max-height: 45dvh; overflow: auto; }
  .map-results button { display: grid; gap: 3px; width: 100%; border: 0; text-align: left; padding: 9px 10px; font-size: 13px; }
  .map-results strong { font-weight: 500; }
  .map-results span { color: var(--muted); font-size: 12px; }
  .map-results p { padding: 10px; font-size: 13px; color: var(--muted); }
  .selected-course { position: absolute; right: 20px; bottom: 24px; width: min(350px, calc(100% - 40px)); padding: 20px; border: 1px solid var(--border); border-radius: 7px; background: var(--bg); }
  .selection-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px; color: var(--accent); }
  .selection-heading button { display: grid; place-items: center; padding: 3px; border: 0; color: var(--muted); }
  h2 { margin: 10px 0; font-size: 21px; font-weight: 500; line-height: 1.3; }
  .selected-course p { font-size: 12px; color: var(--muted); }
  .selected-course > a { display: inline-flex; align-items: center; gap: 6px; margin-top: 16px; font-size: 13px; }
  .map-help { position: absolute; right: 20px; top: 20px; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); max-width: 300px; }
  .map-help summary { list-style: none; cursor: pointer; width: fit-content; margin-left: auto; }
  .map-help summary::-webkit-details-marker { display: none; }
  .map-help p { font-size: 12px; line-height: 1.6; padding: 8px; }
  @media (max-width: 600px) {
    .map-toolbar { top: 12px; left: 12px; width: calc(100% - 24px); }
    .selected-course { right: 12px; bottom: 84px; width: calc(100% - 24px); padding: 16px; }
    .map-help { top: auto; bottom: 28px; right: 16px; }
  }
</style>
