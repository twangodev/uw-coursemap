import type cytoscape from "cytoscape";
import { get } from "svelte/store";
import { mode } from "mode-watcher";
import { clearPath, highlightPath, markNextCourses } from "./paths.ts";
import { getTextColor, getTextOutlineColor } from "$lib/theme.ts";
import { takenCoursesStore } from "$lib/takenCoursesStore.ts";
import { CourseUtils } from "$lib/types/course.ts";
import { isDesktop } from "$lib/mediaStore.ts";
import type { GraphType } from "./graph-styles.ts";

// Scratch namespace for storing app-specific state on cy instance
const SCRATCH_NAMESPACE = "_courseGraph";

interface CourseGraphScratch {
  removedNodes: cytoscape.Collection | null;
}

function getScratch(cy: cytoscape.Core): CourseGraphScratch {
  let scratch = cy.scratch(SCRATCH_NAMESPACE) as CourseGraphScratch | undefined;
  if (!scratch) {
    scratch = { removedNodes: null };
    cy.scratch(SCRATCH_NAMESPACE, scratch);
  }
  return scratch;
}

/**
 * Sets up all handlers for the Cytoscape instance
 * Manages interactions, styling, and state internally via closures
 *
 * @param cy - Cytoscape core instance
 * @param graphType - Type of graph ('department' or 'prereq')
 * @returns Object with control methods
 */
export function setupCytoscapeHandlers(
  cy: cytoscape.Core,
  graphType: GraphType = "department",
) {
  // Interaction state
  let elementsAreDraggable = false;
  let highlightedCourse: cytoscape.NodeSingular | undefined;
  let currentTip: any = undefined;
  let onCourseClickCallback: ((courseId: string) => void) | undefined;

  // Styling state
  let showCodeLabels = true;

  // --- Internal helpers ---

  const destroyTip = () => {
    currentTip?.destroy();
    currentTip = undefined;
  };

  // this function effect is only registered if the graph is department
  const applyThemeAndLabelStyle = () => {
    const currentMode = mode.current;

    cy.style()
      .selector("node")
      .style({
        color: getTextColor(currentMode),
        "text-outline-color": getTextOutlineColor(currentMode),
        "text-outline-opacity": 1,
        "text-outline-width": 1,
        label: showCodeLabels ? "data(id)" : "data(title)",
      })
            .selector(".highlighted-nodes")
      .style({
        "border-color": getTextColor(currentMode),
      })
      .selector("edge")
      .style({
        "line-color": getTextColor(currentMode),
        "target-arrow-color": getTextColor(currentMode),
      })
      .selector(".taken-nodes")
      .style({
        color: currentMode === "dark" ? "#4CC38A" : "#007F44",
      })
      .selector(".next-nodes")
      .style({
        color: currentMode === "dark" ? "#FFD700" : "#B38600",
      })
      .update();
  };

  const applyTakenCoursesStyle = () => {
    const takenCourses = get(takenCoursesStore).map((course) =>
      CourseUtils.courseReferenceToString(course),
    );

    cy.nodes().forEach((node: cytoscape.NodeSingular) => {
      if (takenCourses.includes(node.data("id"))) {
        node.addClass("taken-nodes");
      } else {
        node.removeClass("taken-nodes");
        // Mark courses with no prerequisites as next
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
  };

  const setHiddenSubject = (subject: string | null) => {
    const scratch = getScratch(cy);

    // Restore previously removed nodes
    scratch.removedNodes?.restore();

    // Remove nodes if a subject is hidden
    scratch.removedNodes = subject
      ? cy.nodes(`[parent = "${subject}"]`).remove()
      : null;
  };

  // --- Reactive subscriptions (must be after function definitions) ---

  // Set up reactive subscription using $effect.root for mode changes
  // Only for department graphs - course graphs have fixed colors
  let cleanupModeEffect: (() => void) | undefined;
  if (graphType === "department") {
    cleanupModeEffect = $effect.root(() => {
      $effect(() => {
        // Track mode.current reactively
        mode.current;
        applyThemeAndLabelStyle();
      });
    });
  }

  // Subscribe to taken courses store
  const unsubscribeTakenCourses = takenCoursesStore.subscribe(() => {
    applyTakenCoursesStyle();
  });

  // --- Event handlers ---

  const mouseoverHandler = (event: any) => {
    const targetNode = event.target;
    const nodeType = targetNode?.data("type");
    if (nodeType === "compound" || nodeType === "operator") {
      return;
    }

    if (elementsAreDraggable) {
      targetNode.removeClass("no-overlay");
      targetNode.unpanify();
    } else {
      targetNode.addClass("no-overlay");
      targetNode.panify();
    }

    destroyTip();
    clearPath(cy, () => {});
    highlightPath(cy, targetNode);
  };

  const mouseoutHandler = () => {
    destroyTip();
    clearPath(cy, () => {});

    if (highlightedCourse !== undefined) {
      highlightPath(cy, highlightedCourse);
    }
  };

  const dbltapHandler = (event: any) => {
    const targetNode = event.target;
    const nodeType = targetNode?.data("type");

    if (targetNode.isNode && nodeType !== "compound" && nodeType !== "operator") {
      highlightPath(cy, targetNode);
      highlightedCourse = targetNode;
    } else if (!targetNode.isNode || nodeType === "compound" || nodeType === "operator") {
      clearPath(cy, () => {});
      highlightedCourse = undefined;
    }
  };

  const onetapHandler = async (event: any) => {
    const targetNode = event.target;

    // Only handle nodes with the "course" class (department and prereq course nodes)
    if (!targetNode?.hasClass("course")) {
      return;
    }

    // Desktop: notify parent to open drawer
    if (get(isDesktop)) {
      onCourseClickCallback?.(targetNode.id());
      return;
    }

    // Mobile: create and show tooltip
    const tip = targetNode.popper({
      content: () => {
        const div = document.createElement("div");
        const container = document.createElement("div");
        container.className = "bg-black text-white p-2 rounded-lg";

        const heading = document.createElement("h1");
        heading.className = "text-lg font-semibold";
        heading.textContent = targetNode.id();

        const para = document.createElement("p");
        para.className = "text-sm";
        para.textContent = targetNode.data("description");

        container.appendChild(heading);
        container.appendChild(para);
        div.appendChild(container);
        return div;
      },
    });
    tip.show();
    destroyTip();
    currentTip = tip;
  };

  // Register event handlers
  cy.on("mouseover", "node", mouseoverHandler);
  cy.on("mouseout", "node", mouseoutHandler);
  cy.on("dbltap", dbltapHandler);
  cy.on("onetap", "node", onetapHandler);

  // --- Public API ---

  return {
    onCourseClick(callback: (courseId: string) => void) {
      onCourseClickCallback = callback;
    },

    setElementsAreDraggable(draggable: boolean) {
      elementsAreDraggable = draggable;
    },

    destroyTip,

    setShowCodeLabels(show: boolean) {
      showCodeLabels = show;
      applyThemeAndLabelStyle();
    },

    setHiddenSubject,

    cleanup() {
      cy.off("mouseover", "node", mouseoverHandler);
      cy.off("mouseout", "node", mouseoutHandler);
      cy.off("dbltap", dbltapHandler);
      cy.off("onetap", "node", onetapHandler);
      destroyTip();
      cleanupModeEffect?.();
      unsubscribeTakenCourses();
    },
  };
}
