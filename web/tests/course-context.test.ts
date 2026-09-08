import { describe, expect, it } from "vitest";
import { compareCourse, type PeerCourse } from "../../src/lib/course-context";
const peers: PeerCourse[] = Array.from({ length: 10 }, (_, i) => ({
  uid: `c${i}`,
  code: `COMPSCI ${300 + i}`,
  term: "1264",
  gpa: 2 + i * 0.1,
  count: 30 + i * 10,
  topShare: 50,
  subjects: ["COMPSCI", "ECE"],
}));
describe("course context", () => {
  it("compares only same-term courses and handles cross-list membership", () => {
    const unrelated = [
      { ...peers[0], uid: "other-term", term: "1254" },
      { ...peers[0], uid: "small", count: 29 },
    ];
    const result = compareCourse(peers[5], [...peers, ...unrelated], "ECE")!;
    expect(result.size).toBe(10);
    expect(result.gpaPercentile).toBe(56);
    expect(result.countPercentile).toBe(56);
    expect(result.medianCount).toBe(75);
    expect(result.histogram.reduce((sum, bin) => sum + bin.count, 0)).toBe(10);
    expect(result.histogram.filter((bin) => bin.current)).toHaveLength(1);
  });
  it("does not present a rank for small cohorts or sparse courses", () => {
    expect(compareCourse(peers[0], peers.slice(0, 9))).toBeNull();
    expect(compareCourse({ ...peers[0], count: 29 }, peers)).toBeNull();
  });
  it("does not count ties as lower and includes a 4.0 GPA in the last bin", () => {
    const tied = peers.map((peer) => ({ ...peer, gpa: 4, count: 100 }));
    const result = compareCourse(tied[0], tied)!;
    expect(result.gpaPercentile).toBe(0);
    expect(result.countPercentile).toBe(0);
    expect(result.histogram[9].count).toBe(10);
  });
});
