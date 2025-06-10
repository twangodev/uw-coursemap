<script lang="ts">
  import cytoscape, {
    type Collection,
    type EdgeCollection,
    type ElementDefinition,
    type StylesheetStyle,
  } from "cytoscape";
  import cytoscapeFcose from "cytoscape-fcose";
  import tippy from "tippy.js";
  import cytoscapePopper from "cytoscape-popper";
  import { Progress } from "$lib/components/ui/progress";
  import { cn } from "$lib/utils.ts";
  import {
    courseReferenceToString,
    sanitizeCourseToReferenceString,
    type Course,
  } from "$lib/types/course.ts";
  import { fetchCourse, fetchGraphData } from "./graph-data.ts";
  import { getStyleData, getStyles, type StyleEntry } from "./graph-styles.ts";
  import SideControls from "./side-controls.svelte";
  import CourseDrawer from "./course-drawer.svelte";
  import {
    clearPath,
    getPredecessorsNotTaken,
    highlightPath,
    markNextCourses,
  } from "./paths.ts";
  import { searchModalOpen } from "$lib/searchModalStore.ts";
  import {
    generateFcoseLayout,
    generateLayeredLayout,
    LayoutType,
  } from "$lib/components/cytoscape/graph-layout.ts";
  import { page } from "$app/state";
  import { mode } from "mode-watcher";
  import { getTextColor, getTextOutlineColor } from "$lib/theme.ts";
  import Legend from "./legend.svelte";
  import { onMount } from "svelte";
  import { FileText, Terminal, X } from "@lucide/svelte";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { AlertClose } from "$lib/components/ui/alert";
  import { getData, setData, clearData } from "$lib/localStorage.ts";
  import * as Dialog from "$lib/components/ui/dialog";

  interface Props {
    elementDefinitions: ElementDefinition[];
    styleEntries: StyleEntry[];
    // dfs backwards from a specific course until it reaches courses that are taken
    // courses not reached by dfs are hidden
    filter?: Course;
    allowFocusing?: boolean;
  }

  let cy: cytoscape.Core | undefined = $state();

  let takenCourses: (undefined | string)[] = $state([]);
  let showAlert = $derived(cy && takenCourses.length <= 0);
  let hasSeenTapGuide = $state(false);

  let highlightedCourse = $state<cytoscape.NodeSingular | undefined>();

  onMount(() => {
    loadGraph();
    takenCourses = getData("takenCourses").map((course: any) => {
      if (course.course_reference === undefined) {
        return;
      }

      return courseReferenceToString(course.course_reference);
    });
    hasSeenTapGuide = !(
      getData("hasSeenTapGuide") == undefined ||
      getData("hasSeenTapGuide").length == 0
    );
  });

  let {
    elementDefinitions,
    styleEntries,
    filter = undefined,
    allowFocusing = true,
  }: Props = $props();

  let showCodeLabels = $state(true);
  let styleData = $derived(
    getStyles(styleEntries, mode.current, showCodeLabels),
  );

  let sheetOpen = $state(false);
  let progress = $state({
    text: "Loading Graph...",
    number: 10,
  });

  let focus = $state(page.url.searchParams.get("focus"));

  let cytoscapeStyleData: StyleEntry[] = $state([]);

  let layoutType: LayoutType = $state(LayoutType.LAYERED);

  searchModalOpen.subscribe((isOpen) => {
    if (isOpen) {
      sheetOpen = false;
    }
  });

  let elementsAreDraggable = $state(false);
  const isDesktop = () => window.matchMedia("(min-width: 768px)").matches;

  let selectedCourse: Course | undefined = $state(undefined);

  // Add near your other state declarations

  function tippyFactory(ref: any, content: any) {
    // Since tippy constructor requires DOM element/elements, create a placeholder
    const dummyDomEle = document.createElement("div");

    return tippy(dummyDomEle, {
      getReferenceClientRect: ref.getBoundingClientRect,
      trigger: "manual", // mandatory
      content: content,
      arrow: true,
      placement: "bottom",
      hideOnClick: true,
      sticky: "reference",
      interactive: true,
      appendTo: document.body, // or append dummyDomEle to document.body
    });
  }

  let myTip: any;

  function setTip(newTip: any) {
    myTip?.destroy();
    myTip = newTip;
  }
  function destroyTip() {
    myTip?.destroy();
  }
  const loadGraph = $derived(async () => {
    progress = {
      text: "Fetching Graph Data...",
      number: 25,
    };

    progress = {
      text: "Styling Graph...",
      number: 50,
    };

    progress = {
      text: "Loading Layout...",
      number: 55,
    };

    cytoscape.use(cytoscapeFcose);

    progress = {
      text: "Loading Tooltips...",
      number: 60,
    };

    cytoscape.use(cytoscapePopper(tippyFactory));

    progress = {
      text: "Rendering Graph...",
      number: 65,
    };

    // if you want to use the other layout, just uncomment the one below and comment the other one
    // let newCytoscapeLayout = await generateLayeredLayout(courseData);
    let layout = await computeLayout(layoutType, elementDefinitions, false);

    progress = {
      text: "Graph Loaded",
      number: 99,
    };

    cy = cytoscape({
      container: document.getElementById("cy"),
      elements: elementDefinitions,
      style: styleData,
      layout: layout,
      minZoom: 0.01,
      maxZoom: 2,
      motionBlur: true,
    });

    if (filter !== undefined) {
      let keepData = getPredecessorsNotTaken(
        cy,
        cy.$id(`${courseReferenceToString(filter.course_reference)}`)[0],
        takenCourses,
      );
      const nodesToRemove = cy
        .nodes()
        .filter((node: cytoscape.NodeSingular) => {
          return (
            !keepData.includes(node.id()) && node.data("type") !== "compound"
          );
        });

      cy.remove(nodesToRemove);
    }

    cy.on("mouseover", "node", function (event) {
      const targetNode = event.target;
      if (targetNode?.data("type") === "compound") {
        return;
      }
      if (elementsAreDraggable) {
        targetNode.removeClass("no-overlay");
        targetNode.unpanify();
      } else {
        targetNode.addClass("no-overlay");
        targetNode.panify();
      }

      clearPath(cy, destroyTip);
      highlightPath(cy, targetNode);
    });

    cy.on("mouseout", "node", function (event) {
      clearPath(cy, destroyTip);
      if (highlightedCourse !== undefined) {
        highlightPath(cy, highlightedCourse);
      }
    });

    // keep course highlighted/unhighlighted when double tapping
    cy.on("dbltap", function (event) {
      const targetNode = event.target;

      // If we clicked a node (that isn't a compound node)
      if (targetNode.isNode && targetNode.data("type") !== "compound") {
        highlightedCourse = targetNode;
        highlightPath(cy, targetNode);
      }
      // If we clicked empty space or a compound node
      else if (!targetNode.isNode || targetNode.data("type") === "compound") {
        highlightedCourse = undefined;
        clearPath(cy, destroyTip);
      }
    });

    // open course sheet when single tapping on course
    cy.on("onetap", "node", async function (event) {
      const targetNode = event.target;
      if (targetNode?.data("type") === "compound") {
        return;
      }

      if (isDesktop()) {
        selectedCourse = undefined;

        selectedCourse = await fetchCourse(targetNode.id());
        sheetOpen = true;
        return;
      }

      let tip = targetNode.popper({
        content: () => {
          let div = document.createElement("div");
          div.innerHTML = `
                        <div class="bg-black text-white p-2 rounded-lg">
                            <h1 class="text-lg font-semibold">${targetNode.id()}</h1>
                            <p class="text-sm">${targetNode.data("description")}</p>
                        </div>
                    `;
          return div;
        },
      });
      tip.show();

      setTip(tip);
    });
    const focusParam = page.url.searchParams.get("focus");
    if (focusParam !== null) {
      highlightedCourse = cy?.$id(focusParam.replaceAll("_", " "))[0];
    } else {
      highlightedCourse = undefined;
    }
    progress = {
      text: "Graph Loaded",
      number: 100,
    };
  });

  $effect(() => {
    if (!sheetOpen) {
      focus = null;
    }

    if (!cy) {
      return;
    }
    hide(hiddenSubject);
  });

  async function computeLayout(
    layoutType: LayoutType,
    courseData: ElementDefinition[],
    shouldRun: boolean,
  ) {
    let layout =
      layoutType === LayoutType.GROUPED
        ? generateFcoseLayout(focus)
        : await generateLayeredLayout(focus, courseData, showCodeLabels);

    if (cy && shouldRun) {
      cy.layout(layout).run();
    }

    return layout;
  }

  $effect(() => {
    if (!cy || !takenCourses) {
      return;
    }

    cy.nodes().forEach((node: cytoscape.NodeSingular) => {
      if (takenCourses.includes(node.data("id"))) {
        node.addClass("taken-nodes");
      } else {
        node.removeClass("taken-nodes");
        // this is meant to mark courses with no prerequisites
        // since grad courses don't have prerequisites, we need to check if the course has no incomers and at least one outgoer
        // this is a bit of a hack, but it works for now
        if (
          node.incomers("node").length === 0 &&
          node.outgoers("node").length > 0
        ) {
          node.addClass("next-nodes");
        } else {
          node.removeClass("next-nodes");
        }
      }
    });

    markNextCourses(cy);
  });

  $effect(() => {
    if (!cy) {
      return;
    }
    cy.style()
      .selector("node")
      .style({
        color: getTextColor(mode.current),
        "text-outline-color": getTextOutlineColor(mode.current),
        "text-outline-opacity": 1,
        "text-outline-width": 1,
        label: showCodeLabels ? "data(id)" : "data(title)",
      })
      .selector(".highlighted-nodes")
      .style({
        "border-color": getTextColor(mode.current),
      })
      .selector("edge")
      .style({
        "line-color": getTextColor(mode.current),
        "target-arrow-color": getTextColor(mode.current),
      })
      .selector(".taken-nodes")
      .style({
        color: mode.current === "dark" ? "#4CC38A" : "#007F44",
      })
      .selector(".next-nodes")
      .style({
        color: mode.current === "dark" ? "#FFD700" : "#B38600",
      })
      .update();
  });

  let hiddenSubject = $state(null);

  let removedSubjectNodes: Collection | null;

  function hide(subject: string | null) {
    if (!cy) {
      return;
    }

    removedSubjectNodes?.restore();
    removedSubjectNodes = null;

    if (subject) {
      removedSubjectNodes = cy.nodes(`[parent = "${subject}"]`).remove();
    }
  }
</script>

<div class="relative grow" id="cy-container">
  <div
    class={cn(
      "absolute inset-0 flex flex-col items-center justify-center space-y-4 transition-opacity",
      progress.number === 100 ? "opacity-0" : "",
    )}
  >
    <p class="text-lg font-semibold">{progress.text}</p>
    <Progress class="w-[80%] md:w-[75%] lg:w-[30%]" value={progress.number} />
  </div>
  <div
    id="cy"
    class={cn(
      "h-full w-full transition-opacity",
      progress.number !== 100 ? "opacity-0" : "",
    )}
  ></div>

  <Legend styleEntries={cytoscapeStyleData} bind:hiddenSubject />
  <SideControls
    {cy}
    bind:elementsAreDraggable
    bind:layoutType
    bind:showCodeLabels
    layoutRecompute={(layoutType: LayoutType) => {
      computeLayout(layoutType, elementDefinitions, true);
    }}
  />
</div>
<CourseDrawer
  {cy}
  bind:sheetOpen
  {selectedCourse}
  {destroyTip}
  {allowFocusing}
/>

{#if cy && !hasSeenTapGuide}
  <Dialog.Root open={true}>
    <Dialog.Content class="sm:max-w-md">
      <Dialog.Header>
        <Dialog.Title>Quick Guide</Dialog.Title>
        <Dialog.Description class="space-y-2">
          <p>
            <strong>Single tap on course</strong>: {isDesktop()
              ? "Open detailed course information"
              : "Show course description"}
          </p>
          <p>
            <strong>Double tap on course</strong>: Keeps course prerequisites
            and dependencies highlighted
          </p>
          <p><strong>Double tap on empty space</strong>: Clears highlighting</p>
        </Dialog.Description>
      </Dialog.Header>
      <Dialog.Footer class="flex justify-end">
        <Dialog.Close
          class="ring-offset-background focus-visible:ring-ring bg-primary text-primary-foreground hover:bg-primary/90 inline-flex h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
          onclick={() => {
            hasSeenTapGuide = true;
            setData("hasSeenTapGuide", [true]);
          }}
        >
          Got it
        </Dialog.Close>
      </Dialog.Footer>
    </Dialog.Content>
  </Dialog.Root>
{/if}

{#if showAlert}
  <Alert.Root class="absolute right-15 bottom-28 z-50 w-96">
    <FileText class="h-4 w-4" />
    <Alert.Title>Heads up!</Alert.Title>
    <Alert.Description
      >You can upload your transcript <a
        href="/upload"
        class="text-primary decoration-primary hover:text-primary/80 font-medium underline underline-offset-4 transition-colors"
        >here</a
      > and display courses you've taken in a different color.</Alert.Description
    >
    <p class="mt-2 text-sm">
      <strong
        >We've also trimmed this prerequisite graph to show optimized
        relationships, (i.e. the combination that best satisfies a requisite)</strong
      >
    </p>
    <AlertClose
      class="hover:bg-muted absolute top-2 right-2 rounded-full p-1 opacity-70 transition-opacity hover:opacity-100 md:top-3 md:right-3"
      onclick={() => (showAlert = false)}
    >
      <X class="h-4 w-4" />
      <span class="sr-only">Close</span>
    </AlertClose>
  </Alert.Root>
{/if}
