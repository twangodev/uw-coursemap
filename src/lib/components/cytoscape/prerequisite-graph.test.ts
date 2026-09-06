import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import type { ASTNode, Course } from "$lib/types/course.ts";
import { astToElements } from "./cytoscape-init.ts";
import { createExpandState } from "./expand-state.svelte.ts";
import { fetchCourse, processGraphData } from "./graph-data.ts";
import { generateTreeLayout } from "./graph-layout.ts";

vi.mock("./graph-data.ts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./graph-data.ts")>()),
  fetchCourse: vi.fn(),
}));
vi.mock("./graph-layout.ts", () => ({
  generateTreeLayout: vi.fn(async () => ({ name: "preset", animate: false })),
}));

const ref = (n: number): ASTNode => ({ subjects: ["TEST"], course_number: n });
const and = (...children: ASTNode[]): ASTNode => ({
  operator: "AND",
  children,
});
const or = (...children: ASTNode[]): ASTNode => ({ operator: "OR", children });
const course = (ast: ASTNode) =>
  ({ prerequisites: { abstract_syntax_tree: ast } }) as Course;
const instances: Core[] = [];
function graph(ast: ASTNode) {
  const state = createExpandState(ast, "TEST 999");
  const cy = cytoscape({ headless: true, elements: state.elements });
  instances.push(cy);
  state.setCytoscape(cy);
  cy.emit("layoutstop");
  return { state, cy };
}

beforeEach(() => {
  vi.mocked(fetchCourse).mockReset();
  vi.mocked(generateTreeLayout).mockClear();
});
afterEach(() => {
  for (const cy of instances.splice(0)) cy.destroy();
  vi.restoreAllMocks();
});

describe("prerequisite graph regressions", () => {
  it("renders a target-only graph for null ASTs such as AAE 500 and MS&E 790", () => {
    for (const id of ["AAE 500", "MS&E 790"]) {
      expect(astToElements(null, id)).toMatchObject([
        { data: { id, type: "target" } },
      ]);
    }
  });

  it("ignores null children while keeping valid prerequisites", () => {
    const { cy } = graph(and(null, ref(100)));
    expect(
      cy
        .$id("TEST 100")
        .outgoers("node")
        .map((node) => node.id()),
    ).toEqual(["TEST 999"]);
  });

  it("makes department course nodes hoverable without marking edges or compounds as courses", () => {
    const data: ElementDefinition[] = [
      { data: { id: "TEST 100" }, classes: "existing" },
      { data: { id: "TEST 200" }, classes: ["existing"] },
      { data: { id: "subject", type: "compound" } },
      { data: { id: "edge", source: "TEST 100", target: "TEST 200" } },
    ];
    const cy = cytoscape({
      headless: true,
      elements: processGraphData(processGraphData(data)),
    });
    instances.push(cy);
    expect(cy.nodes(".hoverable.course").map((node) => node.id())).toEqual([
      "TEST 100",
      "TEST 200",
    ]);
    expect(cy.$id("TEST 100").hasClass("existing")).toBe(true);
    expect(cy.$id("TEST 200").hasClass("existing")).toBe(true);
    expect(cy.$id("subject").hasClass("course")).toBe(false);
    expect(cy.$id("edge").hasClass("course")).toBe(false);
  });

  it("preserves a shared required course when hiding its OR alternative", async () => {
    const { state, cy } = graph(and(or(ref(100), ref(200)), ref(200)));
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(300)));
    await state.expandCourse("TEST 100");
    expect(cy.$id("TEST 200").length).toBe(1);
    expect(
      cy
        .$id("TEST 200")
        .outgoers("node")
        .map((node) => node.data("operator")),
    ).toEqual(["AND"]);
    await state.collapseCourse("TEST 100");
    expect(
      cy
        .$id("TEST 200")
        .outgoers("node")
        .map((node) => node.data("operator"))
        .sort(),
    ).toEqual(["AND", "OR"]);
    expect(cy.$id("TEST 300").empty()).toBe(true);
  });

  it("restores a hidden OR subtree, including all of its edges, on collapse", async () => {
    const initial = or(ref(100), and(ref(200), ref(300)));
    const { state, cy } = graph(initial);
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(400)));
    await state.expandCourse("TEST 100");
    expect(cy.$id("TEST 200").empty()).toBe(true);
    expect(cy.$id("TEST 300").empty()).toBe(true);
    await state.collapseCourse("TEST 100");
    expect(state.elements.map((element) => element.data.id).sort()).toEqual(
      astToElements(initial, "TEST 999")
        .map((element) => element.data.id)
        .sort(),
    );
    expect(
      cy
        .$id("TEST 200")
        .successors("node")
        .map((node) => node.id()),
    ).toContain("TEST 999");
  });

  it("retains a shared descendant's expansion after only one parent collapses", async () => {
    const { state, cy } = graph(and(ref(100), ref(200)));
    vi.mocked(fetchCourse).mockImplementation(async (id) =>
      course(id === "TEST 300" ? ref(400) : ref(300)),
    );
    await state.expandCourse("TEST 100");
    await state.expandCourse("TEST 200");
    await state.expandCourse("TEST 300");
    await state.collapseCourse("TEST 100");
    expect(state.isExpanded("TEST 300")).toBe(true);
    expect(
      cy
        .$id("TEST 400")
        .successors("node")
        .map((node) => node.id()),
    ).toContain("TEST 999");
    await state.collapseCourse("TEST 200");
    expect(state.isExpanded("TEST 300")).toBe(false);
    expect(cy.$id("TEST 300").empty()).toBe(true);
    expect(cy.$id("TEST 400").empty()).toBe(true);
  });

  it("waits for animated layout completion before restoring controls and returning", async () => {
    const { state, cy } = graph(ref(100));
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(200)));
    const layout = cy.layout({ name: "preset", animate: false });
    const finishLayout = layout.run.bind(layout);
    vi.spyOn(layout, "run").mockReturnValue(layout);
    vi.spyOn(cy, "layout").mockReturnValueOnce(layout);
    let finished = false;
    const expanding = state.expandCourse("TEST 100").then(() => {
      finished = true;
    });
    await vi.waitFor(() => expect(layout.run).toHaveBeenCalled());
    expect(finished).toBe(false);
    expect(cy.$id("expand-TEST 100").empty()).toBe(true);
    finishLayout();
    await expanding;
    expect(cy.$id("expand-TEST 100").length).toBe(1);
    expect(
      cy
        .$id("TEST 200")
        .outgoers("node")
        .map((node) => node.id()),
    ).toEqual(["expand-TEST 100"]);
  });

  it("keeps previously redirected prerequisite edges across subsequent layouts", async () => {
    const { state, cy } = graph(and(ref(100), ref(200)));
    vi.mocked(fetchCourse).mockImplementation(async (id) =>
      course(ref(id === "TEST 100" ? 300 : 400)),
    );
    await state.expandCourse("TEST 100");
    await state.expandCourse("TEST 200");
    expect(
      cy
        .$id("TEST 300")
        .outgoers("node")
        .map((node) => node.id()),
    ).toEqual(["expand-TEST 100"]);
    await state.collapseCourse("TEST 200");
    expect(
      cy
        .$id("TEST 300")
        .successors("node")
        .map((node) => node.id()),
    ).toContain("TEST 999");
  });

  it("ignores repeated expansion and collapse clicks while a request is in flight", async () => {
    const { state, cy } = graph(ref(100));
    let deliver!: (value: Course) => void;
    vi.mocked(fetchCourse).mockImplementation(
      () =>
        new Promise((resolve) => {
          deliver = resolve;
        }),
    );
    const expanding = state.expandCourse("TEST 100");
    await state.expandCourse("TEST 100");
    await state.collapseCourse("TEST 100");
    expect(fetchCourse).toHaveBeenCalledTimes(1);
    deliver(course(ref(200)));
    await expanding;
    await state.collapseCourse("TEST 100");
    expect(state.isExpanded("TEST 100")).toBe(false);
    expect(cy.$id("TEST 200").empty()).toBe(true);
  });

  it("can retry after a failed fetch", async () => {
    const { state } = graph(ref(100));
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(fetchCourse)
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(course(ref(200)));
    await state.expandCourse("TEST 100");
    expect(state.isExpanded("TEST 100")).toBe(false);
    await state.expandCourse("TEST 100");
    expect(state.isExpanded("TEST 100")).toBe(true);
  });

  it("discards a fetch that completes after the graph is cleared", async () => {
    const { state, cy } = graph(ref(100));
    let deliver!: (value: Course) => void;
    vi.mocked(fetchCourse).mockImplementation(
      () =>
        new Promise((resolve) => {
          deliver = resolve;
        }),
    );
    const expanding = state.expandCourse("TEST 100");
    state.clear();
    deliver(course(ref(200)));
    await expanding;
    expect(state.elements).toEqual([]);
    expect(state.isExpanded("TEST 100")).toBe(false);
    expect(cy.$id("TEST 200").empty()).toBe(true);
  });
  it("rolls back topology and unlocks the graph when layout.run throws", async () => {
    const { state, cy } = graph(ref(100));
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(200)));
    const layout = cy.layout({ name: "preset", animate: false });
    vi.spyOn(layout, "run").mockImplementation(() => {
      throw new Error("layout failed");
    });
    vi.spyOn(cy, "layout").mockReturnValueOnce(layout);
    await state.expandCourse("TEST 100");
    expect(state.isExpanded("TEST 100")).toBe(false);
    expect(cy.$id("TEST 200").empty()).toBe(true);
    await state.expandCourse("TEST 100");
    expect(state.isExpanded("TEST 100")).toBe(true);
  });

  it("blocks other graph mutations until the active layout has completed", async () => {
    const { state, cy } = graph(and(ref(100), ref(200)));
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(300)));
    const layout = cy.layout({ name: "preset", animate: false });
    const finishLayout = layout.run.bind(layout);
    vi.spyOn(layout, "run").mockReturnValue(layout);
    vi.spyOn(cy, "layout").mockReturnValueOnce(layout);
    const expanding = state.expandCourse("TEST 100");
    await vi.waitFor(() => expect(layout.run).toHaveBeenCalled());
    await state.expandCourse("TEST 200");
    await state.collapseCourse("TEST 100");
    expect(fetchCourse).toHaveBeenCalledTimes(1);
    expect(state.isExpanded("TEST 100")).toBe(true);
    finishLayout();
    await expanding;
    await state.expandCourse("TEST 200");
    expect(state.isExpanded("TEST 200")).toBe(true);
  });

  it("settles an outstanding layout when the component is cleared", async () => {
    const { state, cy } = graph(ref(100));
    vi.mocked(fetchCourse).mockResolvedValue(course(ref(200)));
    const layout = cy.layout({ name: "preset", animate: false });
    vi.spyOn(layout, "run").mockReturnValue(layout);
    vi.spyOn(cy, "layout").mockReturnValueOnce(layout);
    const expanding = state.expandCourse("TEST 100");
    await vi.waitFor(() => expect(layout.run).toHaveBeenCalled());
    state.clear();
    await expanding;
    expect(state.elements).toEqual([]);
    expect(cy.$id("expand-TEST 100").empty()).toBe(true);
  });
});
