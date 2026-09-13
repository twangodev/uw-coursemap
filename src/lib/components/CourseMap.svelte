<script lang="ts">
  import { onMount } from "svelte";
  import { Plus, Minus, Maximize2, RotateCw } from "@lucide/svelte";
  import cytoscape, { type Core, type StylesheetStyle } from "cytoscape";
  import ELK from "elkjs/lib/elk-api.js";
  import elkWorkerUrl from "elkjs/lib/elk-worker.min.js?url";
  import { layeredGraph } from "$lib/course-map-layout";
  import type { CourseMapData } from "$lib/course-map";
  let {
    data,
    focus = "",
    subject,
    onSelect,
  }: {
    data: CourseMapData;
    focus?: string;
    subject?: string | null;
    onSelect: (uid: string) => void;
  } = $props();
  let container: HTMLDivElement;
  let cy = $state.raw<Core | null>(null);
  let ready = $state(false);
  let error = $state("");
  let worker: InstanceType<typeof ELK> | undefined;

  function displayCode(course: CourseMapData["courses"][number]) {
    const prefix =
      subject && course.subjects.includes(subject)
        ? subject
        : course.subjects[0];
    return prefix ? `${prefix} ${course.code.split(" ").at(-1)}` : course.code;
  }
  function styles(): StylesheetStyle[] {
    const css = getComputedStyle(document.documentElement);
    const color = (name: string) => css.getPropertyValue(name).trim();
    return [
      {
        selector: "node",
        style: {
          shape: "ellipse",
          width: 16,
          height: 16,
          "background-color": color("--bg"),
          "border-color": color("--accent"),
          "border-width": 2,
          label: "data(code)",
          "font-family": "Overused Grotesk",
          "font-size": 15,
          color: color("--text"),
          "text-valign": "bottom",
          "text-margin-y": 7,
          "min-zoomed-font-size": 5,
          "text-background-color": color("--bg"),
          "text-background-opacity": 0.85,
          "text-background-padding": "2px",
        },
      },
      {
        selector: "edge",
        style: {
          width: 1,
          "line-color": color("--muted"),
          "target-arrow-color": color("--muted"),
          "target-arrow-shape": "triangle",
          "arrow-scale": 0.65,
          "curve-style": "bezier",
          opacity: 0.35,
        },
      },
      { selector: ".faded", style: { opacity: 0.12 } },
      {
        selector: "node.connected",
        style: {
          "background-color": color("--accent-soft"),
          "min-zoomed-font-size": 0,
        },
      },
      {
        selector: "edge.connected",
        style: {
          "curve-style": "bezier",
          "line-color": color("--accent"),
          "target-arrow-color": color("--accent"),
          opacity: 0.8,
          width: 1.5,
        },
      },
      {
        selector: "node.focused",
        style: {
          width: 23,
          height: 23,
          "background-color": color("--accent"),
          "font-weight": 600,
          "min-zoomed-font-size": 0,
        },
      },
    ];
  }
  function fit() {
    cy?.fit(undefined, 70);
  }
  function zoom(factor: number) {
    if (cy)
      cy.zoom({
        level: cy.zoom() * factor,
        renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
      });
  }
  function arrange() {
    ready = false;
    error = "";
    worker?.terminateWorker();
    const engine = new ELK({ workerUrl: elkWorkerUrl });
    worker = engine;
    engine
      .layout(
        layeredGraph({
          courses: data.courses.map((course) => ({
            ...course,
            code: displayCode(course),
          })),
          edges: data.edges,
        }),
      )
      .then((graph) => {
        if (worker !== engine || !cy) return;
        const positions = new Map(
          (graph.children || []).map((node) => [
            node.id,
            {
              x: (node.x || 0) + (node.width || 0) / 2,
              y: (node.y || 0) + 8,
            },
          ]),
        );
        cy.nodes().positions((node) => positions.get(node.id())!);
        ready = true;
        fit();
      })
      .catch((reason) => {
        if (worker === engine)
          error =
            reason instanceof Error
              ? reason.message
              : "The map could not be arranged. Try again.";
      })
      .finally(() => engine.terminateWorker());
  }
  onMount(() => {
    cy = cytoscape({
      container,
      elements: [
        ...data.courses.map((course) => ({
          data: { id: course.uid, code: displayCode(course) },
        })),
        ...data.edges.map((edge) => ({
          data: { ...edge, id: `${edge.source}:${edge.target}` },
        })),
      ],
      style: styles(),
      layout: { name: "grid" },
      minZoom: 0.005,
      maxZoom: 3,
      wheelSensitivity: 0.2,
      pixelRatio: Math.min(devicePixelRatio, 2),
      textureOnViewport: true,
      boxSelectionEnabled: false,
    });
    cy.on("tap", "node", (event) => onSelect(event.target.id()));
    cy.on("tap", (event) => {
      if (event.target === cy) onSelect("");
    });
    const resize = new ResizeObserver(() => cy?.resize());
    resize.observe(container);
    const theme = new MutationObserver(() => cy?.style(styles()));
    theme.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    arrange();
    return () => {
      worker?.terminateWorker();
      resize.disconnect();
      theme.disconnect();
      cy?.destroy();
      cy = null;
    };
  });
  $effect(() => {
    if (!cy || !ready) return;
    const selected = cy.getElementById(focus);
    cy.batch(() => {
      cy!.elements().removeClass("faded connected focused");
      if (selected.length) {
        const neighborhood = selected.closedNeighborhood();
        cy!.elements().not(neighborhood).addClass("faded");
        neighborhood.addClass("connected");
        selected.addClass("focused");
      }
    });
    if (selected.length) {
      cy.fit(selected.closedNeighborhood(), 120);
      const level = Math.max(
        cy.width() < 600 ? 0.8 : 0.75,
        Math.min(1.3, cy.zoom()),
      );
      if (cy.zoom() !== level) {
        cy.zoom(level);
        cy.center(selected);
      }
    }
  });
</script>

<div
  class="inset-0 bg-canvas map"
  bind:this={container}
  role="img"
  aria-label={`Course prerequisite map: ${data.courses.length} courses, ${data.edges.length} connections`}
  data-ready={ready}
  data-node-count={data.courses.length}
></div>
{#if !ready}<div
    class="absolute left-1/2 top-1/2 border border-border rounded-[6px] bg-canvas text-[14px] map-status py-4 px-5"
    role="status"
  >
    {error ||
      `Arranging ${data.courses.length.toLocaleString()} courses…`}{#if error}<button
        class="block mt-3"
        onclick={arrange}>Try again</button
      >{/if}
  </div>{/if}
<div
  class="absolute left-5 bottom-6 flex gap-[1px] p-1 border border-border rounded-[6px] bg-canvas map-controls"
  aria-label="Map controls"
>
  <button
    class="grid place-items-center w-9 h-9 border-0 p-0"
    aria-label="Zoom in"
    onclick={() => zoom(1.3)}><Plus size={17} /></button
  >
  <button
    class="grid place-items-center w-9 h-9 border-0 p-0"
    aria-label="Zoom out"
    onclick={() => zoom(1 / 1.3)}><Minus size={17} /></button
  >
  <button
    class="grid place-items-center w-9 h-9 border-0 p-0"
    aria-label="Fit all courses"
    onclick={() => {
      onSelect("");
      fit();
    }}><Maximize2 size={17} /></button
  >
  <button
    class="grid place-items-center w-9 h-9 border-0 p-0"
    aria-label="Rearrange map"
    onclick={arrange}
    disabled={!ready && !error}><RotateCw size={16} /></button
  >
</div>

<style>
  /* Cytoscape injects an unlayered position: relative rule on its container. */
  .map {
    position: absolute;
  }
  .map-status {
    transform: translate(-50%, -50%);
  }
</style>
