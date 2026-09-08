import { expect, it } from "vitest";
import { instructorSeries, instructorChartRows, gradeTrendDomain } from "../../src/lib/instructor-trends";
it("weights instructor GPA by letter grades and leaves missing terms as gaps", () => {
  const lines = instructorSeries([
    { instructor_uid: "a", term: "1252", a: 10, f: 30 },
    { instructor_uid: "a", term: "1262", a: 40 },
    { instructor_uid: "b", term: "1252", a: 10 },
    { instructor_uid: "empty", term: "1252", satisfactory: 100 },
  ], new Map([["a", "First"], ["b", "Second"]]));
  expect(lines).toHaveLength(2);
  expect(lines[0].terms[0].gpa).toBe(1);
  expect(lines[0].count).toBe(80);
  const rows = instructorChartRows([{ term: "1252", gpa: 2 }, { term: "1254", gpa: 3 }, { term: "1262", gpa: 3.5 }], lines);
  expect(rows[1].a).toBeNull();
  expect(rows[1].b).toBeNull();
  expect(rows[2].overall).toBe(3.5);
});

it("fits only plotted values and pads constant GPA at scale boundaries", () => {
  expect(gradeTrendDomain([{ overall: 3.2, instructor: 3.5, hidden: 0 }, { overall: null }], ["overall", "instructor"])).toEqual([3.1, 3.6]);
  expect(gradeTrendDomain([{ value: 4 }], ["value"])).toEqual([3.9, 4]);
  expect(gradeTrendDomain([{ value: 0 }], ["value"])).toEqual([0, 0.1]);
  expect(gradeTrendDomain([], [])).toEqual([0, 4]);
});
