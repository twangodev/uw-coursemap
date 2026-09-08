import { describe, it, expect, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: true }));
import {
  search,
  gradeRows,
  assertRevision,
  status,
} from "../../src/lib/server/data";
import { normalize, termName, safeUrl } from "../../src/lib/format";
import { visibleTree } from "../../src/lib/requirements";
describe("course discovery", () => {
  it("normalizes student course aliases", () => {
    expect(normalize("CS 300")).toBe("COMPSCI300");
    expect(normalize("COMP SCI 300")).toBe("COMPSCI300");
  });
  it("ranks exact course codes first", async () => {
    for (const q of ["CS300", "CS 300", "COMP SCI 300"]) {
      const r = await search(
        new URL("http://localhost/search?q=" + encodeURIComponent(q)),
      );
      expect(r.items[0].course_id).toBe("COMPSCI 300");
    }
  });
  it("finds partial cross-list aliases", async () => {
    const r = await search(new URL("http://localhost/search?q=CS%2FECE%20759"));
    expect(r.items.some((c) => c.course_id.includes("759"))).toBe(true);
  });
  it("combines full text and department filters", async () => {
    const r = await search(
      new URL("http://localhost/search?q=programming&subject=COMPSCI"),
    );
    expect(r.items.some((c) => c.course_id === "COMPSCI 300")).toBe(true);
  });
  it("rejects malformed filters and pagination", async () => {
    await expect(
      search(new URL("http://localhost/search?gpa_min=nope")),
    ).rejects.toMatchObject({ status: 400 });
    await expect(
      search(new URL("http://localhost/search?page=-1")),
    ).rejects.toMatchObject({ status: 400 });
  });
  it("rejects mixed revisions", async () => {
    await expect(
      assertRevision(new URL("http://localhost/api/search?revision=old")),
    ).rejects.toMatchObject({ status: 409 });
  });
  it("queries current instructor names", async () => {
    const r = await search(
      new URL("http://localhost/search?kind=instructor&q=Hobbes"),
    );
    expect(r.items.some((i) => i.name.includes("Hobbes"))).toBe(true);
  });
  it("uses course distributions separately from instructor sections", async () => {
    const r = await gradeRows(
      "course_28c3390ba944d49fd17f7c72",
      new URL("http://localhost/api"),
    );
    expect(r.items.length).toBeGreaterThan(0);
    expect(r.items.every((g) => !g.grade_section_uid)).toBe(true);
  });
});
describe("presentation integrity", () => {
  it("formats academic term codes", () => {
    expect(termName("1272")).toBe("Fall 2026");
    expect(termName("1264")).toBe("Spring 2026");
  });
  it("does not render executable source URLs", () => {
    expect(safeUrl("javascript:alert(1)")).toBeUndefined();
    expect(safeUrl("https://example.com")).toBe("https://example.com/");
  });
  it("bounds graph traversal and retains condition nodes", () => {
    const ast = {
      root: "r",
      nodes: [
        { id: "r", kind: "any", children: ["a", "r"] },
        {
          id: "a",
          kind: "condition",
          condition: "Standing required",
          children: [],
        },
      ],
    };
    const graph = visibleTree(ast, new Set(["r"]));
    expect(graph.nodes).toHaveLength(2);
    expect(graph.edges).toHaveLength(1);
  });
});


it("ranks eligible courses in both directions and rejects unknown collections", async () => {
  for (const ranking of ["easiest", "hardest"]) {
    const result = await search(new URL(`http://localhost/search?ranking=${ranking}&subject=COMPSCI&sort=gpa`));
    expect(result.items.length).toBeGreaterThan(2);
    expect(result.items.every(c => c.discovery.history.count >= 100)).toBe(true);
    const gpas = result.items.map(c => c.discovery.history.gpa);
    expect(gpas).toEqual([...gpas].sort((a, b) => ranking === "easiest" ? b - a : a - b));
    expect(result.items.every(c => c.course_id.includes("COMPSCI"))).toBe(true);
  }
  await expect(search(new URL("http://localhost/search?ranking=unknown"))).rejects.toMatchObject({ status: 400 });
});
