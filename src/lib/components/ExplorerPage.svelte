<script lang="ts">
  import { onMount } from "svelte";
  import { ArrowLeft, ArrowUpRight, Search, X, Info } from "@lucide/svelte";
  import { courseUrl, normalize, courseTitle } from "$lib/format";
  import { departmentName } from "$lib/departments";
  import type { CourseMapData } from "$lib/course-map";
  let { data }: { data: { subject: string | null; graph: CourseMapData } } =
    $props();
  let Graph = $state<any>(null);
  let query = $state("");
  let chosen = $state("");
  let loadError = $state(false);
  let candidates = $derived(
    query.trim()
      ? data.graph.courses
          .filter((course) =>
            normalize(`${course.code} ${course.title}`).includes(
              normalize(query),
            ),
          )
          .sort(
            (a, b) =>
              Number(normalize(b.code) === normalize(query)) -
                Number(normalize(a.code) === normalize(query)) ||
              a.code.localeCompare(b.code),
          )
          .slice(0, 8)
      : [],
  );
  let selected = $derived(
    data.graph.courses.find((course) => course.uid === chosen),
  );
  let incoming = $derived(
    data.graph.edges.filter((edge) => edge.target === chosen).length,
  );
  let outgoing = $derived(
    data.graph.edges.filter((edge) => edge.source === chosen).length,
  );
  let title = $derived(
    data.subject
      ? `${departmentName(data.subject)} prerequisite map`
      : "Course prerequisite map",
  );
  function select(uid: string) {
    chosen = uid;
    query = "";
  }
  onMount(() => {
    const requested = new URL(location.href).searchParams.get("course");
    if (requested)
      chosen =
        data.graph.courses.find(
          (course) => normalize(course.code) === normalize(requested),
        )?.uid || "";
    import("./CourseMap.svelte")
      .then((module) => (Graph = module.default))
      .catch(() => (loadError = true));
  });
</script>

<div class="relative w-full h-[100dvh] overflow-hidden explorer">
  {#if Graph}<Graph
      data={data.graph}
      subject={data.subject}
      focus={chosen}
      onSelect={select}
    />{:else}<p
      class="absolute inset-[50%_0_auto] text-center text-muted loading"
      role="status"
    >
      {loadError
        ? "Unable to load the map. Reload to try again."
        : "Loading prerequisite map…"}
    </p>{/if}
  <div
    class="absolute top-5 left-5 w-[min(420px,_calc(100%_-_40px))] border border-border rounded-[7px] bg-canvas shadow-[0_3px_18px_#00000008] map-toolbar"
  >
    <div class="flex items-center gap-3 p-4 map-heading">
      <a
        class="grid place-items-center text-muted back"
        href={data.subject
          ? `/departments/${encodeURIComponent(data.subject)}`
          : "/departments"}
        aria-label="Department courses & statistics"><ArrowLeft size={17} /></a
      >
      <a class="flex shrink-0 map-brand" href="/" aria-label="UW Courses home"
        ><img src="/uwcourses-logo.svg" alt="" width="24" height="24" /></a
      >
      <div>
        <h1
          class="text-[16px] leading-[1.25] font-[550] tracking-[-0.02em] m-0"
        >
          {title}
        </h1>
        <p class="mt-[5px] mb-0 text-[12px] text-muted mx-0">
          {data.graph.courses.length.toLocaleString()} courses · {data.graph.edges.length.toLocaleString()}
          connections
        </p>
      </div>
    </div>
    <div
      class="flex items-center gap-2.5 border-t border-t-border text-muted map-search py-0 px-4"
    >
      <Search size={16} />
      <input
        class="min-w-0 w-full border-0 rounded-none bg-transparent text-[14px] py-3 px-0"
        aria-label="Find a course on the map"
        type="search"
        placeholder="Find a course…"
        bind:value={query}
        onkeydown={(event) => {
          if (event.key === "Escape") query = "";
          if (event.key === "Enter" && candidates[0]) select(candidates[0].uid);
        }}
      />
    </div>
    {#if query.trim()}<div
        class="border-t border-t-border p-1.5 max-h-[45dvh] overflow-auto map-results"
        aria-label="Matching courses"
      >
        {#each candidates as course}<button
            class="grid gap-[3px] w-full border-0 text-left text-[13px] py-[9px] px-2.5"
            onclick={() => select(course.uid)}
            aria-label={course.code}
            ><strong class="font-medium">{course.code}</strong><span
              class="text-muted text-[12px]">{courseTitle(course.title)}</span
            ></button
          >{:else}<p class="p-2.5 text-[13px] text-muted">
            No matching courses.
          </p>{/each}
      </div>{/if}
  </div>
  {#if selected}<aside
      class="absolute right-5 bottom-6 w-[min(350px,_calc(100%_-_40px))] p-5 border border-border rounded-[7px] bg-canvas selected-course"
      aria-label="Selected course"
    >
      <div
        class="flex items-center justify-between gap-3 text-[13px] text-accent selection-heading"
      >
        <span>{selected.code}</span><button
          class="grid place-items-center p-[3px] border-0 text-muted"
          aria-label="Clear selected course"
          onclick={() => select("")}><X size={16} /></button
        >
      </div>
      <h2 class="text-[21px] font-medium leading-[1.3] my-2.5 mx-0">
        {courseTitle(selected.title)}
      </h2>
      <p class="text-[12px] text-muted">
        {incoming} prerequisite references · {outgoing} following courses
      </p>
      <a
        class="inline-flex items-center gap-1.5 mt-4 text-[13px]"
        href={courseUrl(selected.code)}
        >Open course <ArrowUpRight size={15} /></a
      >
    </aside>{/if}
  <details
    class="absolute right-5 top-5 p-2 border border-border rounded-[6px] bg-canvas max-w-75 map-help"
  >
    <summary
      class="list-none cursor-pointer w-fit ml-auto"
      aria-label="About this map"><Info size={17} /></summary
    >
    <p class="text-[12px] leading-[1.6] p-2">
      Drag to pan; scroll or pinch to zoom. Select a course to highlight its
      connections. Arrows point from a prerequisite reference to the course that
      mentions it. Alternatives are included; open the course for complete
      requirements and exclusions.
    </p>
  </details>
</div>

<style>
  .map-help summary::-webkit-details-marker {
    display: none;
  }
  @media (max-width: 600px) {
    .map-toolbar {
      top: 12px;
      left: 12px;
      width: calc(100% - 24px);
    }
    .selected-course {
      right: 12px;
      bottom: 84px;
      width: calc(100% - 24px);
      padding: 16px;
    }
    .map-help {
      top: auto;
      bottom: 28px;
      right: 16px;
    }
  }
</style>
