import { describe, it, expect, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: true }));
import { gradeSummary } from "../../src/lib/discovery";
import { search, query } from "../../src/lib/server/data";
import { departmentStats } from "../../src/lib/server/departments";
import { instructorReviews } from "../../src/lib/server/reviews";
describe("student discovery", () => {
  it("weights grades and excludes non-letter outcomes", () => {
    const s = gradeSummary([
      { term: "1262", a: 10, f: 30, satisfactory: 100 },
      { term: "1264", a: 40 },
    ]);
    expect(s.count).toBe(80);
    expect(s.gpa).toBe(2.5);
    expect(s.topShare).toBe(62.5);
  });
  it("respects offering, level and historical cutoffs", async () => {
    const found = await search(
      new URL(
        "http://localhost/search?subject=COMPSCI&level=300&term=1264&availability=all",
      ),
    );
    expect(found.items.length).toBeGreaterThan(0);
    for (const course of found.items) {
      expect((course.discovery.history.lastTerm || "") <= "1264").toBe(true);
      expect(course.course_id).toMatch(/3\d\d/);
    }
    const offered = await search(
      new URL("http://localhost/search?subject=COMPSCI"),
    );
    expect(offered.items.every((row: any) => row.discovery.offered)).toBe(true);
  });
  it("does not sum repeated section distributions into department totals", async () => {
    const stats = await departmentStats("COMPSCI");
    const [expected] = await query(
      undefined,
      "SELECT SUM(a+ab+b+bc+c+d+f) n FROM grade_summaries g JOIN subjects s ON s.uid=g.uid WHERE s.subject='COMPSCI'",
    );
    expect(stats.all.count).toBe(expected.n);
    expect(stats.all.levels.reduce((n, row) => n + row.count, 0)).toBe(
      expected.n,
    );
  });
  it("paginates deduplicated reviews and filters by mapped course", async () => {
    const [profile] = await query(
      undefined,
      "SELECT uid FROM instructors WHERE json_extract(payload,'$.ratings.review_count')>12 LIMIT 1",
    );
    const a = await instructorReviews(profile.uid),
      b = await instructorReviews(profile.uid, 2);
    expect(a.items).toHaveLength(6);
    expect(b.items).toHaveLength(6);
    expect(
      new Set([...a.items, ...b.items].map((r) => r.source_review_id)).size,
    ).toBe(12);
    if (a.courses.length) {
      const filtered = await instructorReviews(
        profile.uid,
        1,
        a.courses[0].course_uid,
      );
      expect(
        filtered.items.every((r) => r.course_uid === a.courses[0].course_uid),
      ).toBe(true);
    }
  });
});
