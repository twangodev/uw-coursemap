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
  import HelpControl from "./help-control.svelte";
  import { getData } from "$lib/localStorage.ts";
  import { m } from "$lib/paraglide/messages";

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

  let highlightedCourse = $state<cytoscape.NodeSingular | undefined>();

  onMount(() => {
    loadGraph();
    takenCourses = getData("takenCourses").map((course: any) => {
      if (course.course_reference === undefined) {
        return;
      }

      return courseReferenceToString(course.course_reference);
    }) 
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
    text: m["cytoscape.progress.loadingGraph"](),
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
  let isDesktopValue = $state(false);
  
  $effect(() => {
    isDesktopValue = window.matchMedia("(min-width: 768px)").matches;
  });
  
  const isDesktop = () => isDesktopValue;

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
      text: m["cytoscape.progress.fetchingData"](),
      number: 25,
    };

    progress = {
      text: m["cytoscape.progress.stylingGraph"](),
      number: 50,
    };

    progress = {
      text: m["cytoscape.progress.loadingLayout"](),
      number: 55,
    };

    cytoscape.use(cytoscapeFcose);

    progress = {
      text: m["cytoscape.progress.loadingTooltips"](),
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
  <HelpControl isDesktop={isDesktopValue} />
</div>
<CourseDrawer
  {cy}
  bind:sheetOpen
  {selectedCourse}
  {destroyTip}
  {allowFocusing}
/>

