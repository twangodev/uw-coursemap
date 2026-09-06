/** State and layout for expandable prerequisite graphs. */
import type { Core, ElementDefinition } from "cytoscape";
import type { ASTNode } from "$lib/types/course.ts";
import { astToElements } from "./cytoscape-init.ts";
import { fetchCourse } from "./graph-data.ts";
import { generateTreeLayout } from "./graph-layout.ts";

const EXPAND_OFFSET = 40;
// Cytoscape mutates data objects when edges move; never give it canonical data.
const copyElement = (element: ElementDefinition): ElementDefinition => ({
  ...element,
  data: { ...element.data },
});
const isEdge = (element: ElementDefinition) =>
  !!element.data.source && !!element.data.target;

export function createExpandState(initialAst: ASTNode, targetCourseId: string) {
  const initialElements = astToElements(initialAst, targetCourseId);
  let coreElements = $state<ElementDefinition[]>(initialElements);
  const expandedCourses = new Map<string, ElementDefinition[]>();
  let cyInstance: Core | null = null;
  let busy = false;
  let generation = 0;
  let cancelLayout: (() => void) | undefined;
  let detachInitialLayout: (() => void) | undefined;

  // Keep canonical edges pointed at courses. Expand controls are only a visual
  // presentation; hiding an OR alternative must not delete a shared course.
  function visibleElements(): ElementDefinition[] {
    const elements = new Map<string, ElementDefinition>();
    for (const element of initialElements)
      elements.set(element.data.id!, element);
    for (const [courseId, expansion] of expandedCourses) {
      for (const element of expansion) {
        if (element.data.id !== courseId && !elements.has(element.data.id!)) {
          elements.set(element.data.id!, element);
        }
      }
    }

    const edges = [...elements.values()].filter(isEdge);
    const selectedOperators = new Set<string>();
    for (const { data } of edges) {
      if (
        elements.get(data.target!)?.data.operator === "OR" &&
        expandedCourses.has(data.source!)
      ) {
        selectedOperators.add(data.target!);
      }
    }
    const incoming = new Map<string, ElementDefinition[]>();
    for (const edge of edges) {
      const { source, target } = edge.data;
      if (!elements.has(source!) || !elements.has(target!)) continue;
      if (selectedOperators.has(target!) && !expandedCourses.has(source!))
        continue;
      const list = incoming.get(target!) ?? [];
      list.push(edge);
      incoming.set(target!, list);
    }

    const visible = new Set<string>();
    const visit = (id: string) => {
      if (visible.has(id)) return;
      visible.add(id);
      for (const edge of incoming.get(id) ?? []) {
        visible.add(edge.data.id!);
        visit(edge.data.source!);
      }
    };
    visit(targetCourseId);
    return [...elements.values()].filter((element) =>
      visible.has(element.data.id!),
    );
  }

  function rebuildElements() {
    coreElements = visibleElements();
    // A collapsed branch releases only expansions that have no remaining path
    // to the target. Shared descendants keep their expansion state.
    const visible = new Set(
      coreElements
        .filter((element) => !isEdge(element))
        .map((element) => element.data.id),
    );
    let removed = false;
    for (const courseId of expandedCourses.keys()) {
      if (!visible.has(courseId)) {
        expandedCourses.delete(courseId);
        removed = true;
      }
    }
    if (removed) coreElements = visibleElements();
  }

  function syncElements(cy: Core) {
    const ids = new Set(coreElements.map((element) => element.data.id));
    cy.batch(() => {
      cy.remove('node[type="expand"]');
      cy.remove(cy.elements().filter((element) => !ids.has(element.id())));
      // Removing controls also removes edges visually redirected to them.
      // Restore all missing canonical edges after adding their endpoints.
      for (const edges of [false, true]) {
        for (const element of coreElements) {
          if (isEdge(element) === edges && cy.$id(element.data.id!).empty())
            cy.add(copyElement(element));
        }
      }
    });
  }

  function addExpandNodes(cy: Core) {
    const courseIds = new Set(expandedCourses.keys());
    cy.nodes('[type="prereq"]').forEach((node) => {
      if (node.incomers('edge[type!="expand-edge"]').empty())
        courseIds.add(node.id());
    });
    for (const courseId of courseIds) {
      const node = cy.$id(courseId);
      if (node.empty() || !cy.$id(`expand-${courseId}`).empty()) continue;
      cy.add([
        {
          data: {
            id: `expand-${courseId}`,
            label: expandedCourses.has(courseId) ? "-" : "+",
            type: "expand",
            targetCourseId: courseId,
          },
          position: {
            x: node.position().x - EXPAND_OFFSET,
            y: node.position().y,
          },
        },
        {
          data: {
            id: `expand-edge-${courseId}`,
            source: `expand-${courseId}`,
            target: courseId,
            type: "expand-edge",
          },
        },
      ]);
    }
    for (const [courseId, expansion] of expandedCourses) {
      if (cy.$id(`expand-${courseId}`).empty()) continue;
      for (const element of expansion) {
        if (isEdge(element) && element.data.target === courseId) {
          cy.$id(element.data.id!).move({ target: `expand-${courseId}` });
        }
      }
    }
  }

  async function runLayout(cy: Core) {
    syncElements(cy);
    const options = await generateTreeLayout(true, coreElements, true);
    if (cy !== cyInstance || cy.destroyed()) return;
    const layout = cy.layout(options);
    await new Promise<void>((resolve, reject) => {
      const cleanup = () => {
        layout.off("layoutstop", finish);
        cy.off("destroy", finish);
        if (cancelLayout === finish) cancelLayout = undefined;
      };
      const finish = () => {
        cleanup();
        resolve();
      };
      cancelLayout = finish;
      layout.one("layoutstop", finish);
      cy.one("destroy", finish);
      try {
        layout.run();
      } catch (error) {
        cleanup();
        reject(error);
      }
    });
    if (cy === cyInstance && !cy.destroyed()) addExpandNodes(cy);
  }

  // Serialize graph mutations through fetch and animation, including clicks on
  // different courses. A second operation cannot remove an active layout's nodes.
  async function update(courseId: string, expand: boolean) {
    const cy = cyInstance;
    if (!cy || cy.destroyed() || busy || cy.$id(courseId).empty()) return;
    if (expandedCourses.has(courseId) === expand) return;
    busy = true;
    const currentGeneration = generation;
    const previous = new Map(expandedCourses);
    try {
      if (expand) {
        const course = await fetchCourse(courseId);
        if (
          currentGeneration !== generation ||
          cy !== cyInstance ||
          cy.destroyed()
        )
          return;
        const ast = course.prerequisites?.abstract_syntax_tree;
        if (!ast) return;
        expandedCourses.set(courseId, astToElements(ast, courseId));
      } else {
        expandedCourses.delete(courseId);
      }
      rebuildElements();
      await runLayout(cy);
    } catch (error) {
      if (
        currentGeneration === generation &&
        cy === cyInstance &&
        !cy.destroyed()
      ) {
        expandedCourses.clear();
        for (const [id, elements] of previous)
          expandedCourses.set(id, elements);
        rebuildElements();
        syncElements(cy);
        addExpandNodes(cy);
      }
      console.error(
        `Failed to ${expand ? "expand" : "collapse"} ${courseId}:`,
        error,
      );
    } finally {
      if (currentGeneration === generation) busy = false;
    }
  }

  return {
    get elements() {
      return coreElements.map(copyElement);
    },
    setCytoscape(cy: Core) {
      detachInitialLayout?.();
      cyInstance = cy;
      const ready = () => {
        if (cy === cyInstance && !cy.destroyed()) addExpandNodes(cy);
      };
      cy.one("layoutstop", ready);
      detachInitialLayout = () => cy.off("layoutstop", ready);
    },
    expandCourse: (courseId: string) => update(courseId, true),
    collapseCourse: (courseId: string) => update(courseId, false),
    isExpanded: (courseId: string) => expandedCourses.has(courseId),
    clear() {
      generation++;
      detachInitialLayout?.();
      cancelLayout?.();
      detachInitialLayout = undefined;
      cyInstance = null;
      busy = false;
      coreElements = [];
      expandedCourses.clear();
    },
  };
}

export type ExpandState = ReturnType<typeof createExpandState>;
