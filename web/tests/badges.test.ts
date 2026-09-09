import { describe, expect, it } from 'vitest';
import { instructorBadges, courseBadges } from '../../src/lib/badges';
const ratings = { bayesian_quality: 4, quality_count: 10, difficulty: 3.5, difficulty_count: 10 };
const course = { course_id: 'COMPSCI 300', semester: '1272', sections: [
  { term_id: '1272', section_type: 'LEC', section_uid: 'a', enrolled: 30 },
  { term_id: '1272', section_type: 'LEC', section_uid: 'a', enrolled: 30 },
  { term_id: '1272', section_type: 'DIS', section_uid: 'b', enrolled: 1 },
] };
const context = { terms: { '1264': { gpa: 3.5, count: 30 }, '1272': null }, benchmarks: { terms: { '1264': { school: { gpa: 3, size: 100 }, COMPSCI: { gpa: 3.8, size: 10 } } } } };
const instructors = [{ name: 'Teacher', instructor_url: '/instructors/Teacher', ratings, terms: [{ term: '1272' }] }];
const get = (overrides = {}) => courseBadges({ course, context, term: '1272', instructors, ...overrides });
describe('student badges', () => {
  it('allows quality and difficulty to coexist at exact thresholds', () => expect(instructorBadges(ratings).map(b => b.label)).toEqual(['Highly rated', 'Challenging']));
  it('checks unrounded values and independent sample sizes', () => {
    expect(instructorBadges({ ...ratings, bayesian_quality: 3.999, difficulty_count: 9 })).toEqual([]);
    expect(instructorBadges({ ...ratings, quality_count: 9 })).toHaveLength(1);
    expect(instructorBadges({ bayesian_quality: NaN, quality_count: 50 })).toEqual([]);
    expect(instructorBadges(null)).toEqual([]);
  });
  it('orders highlights and deduplicates teachers and lecture sections', () => {
    const badges = get({ instructors: [...instructors, ...instructors] });
    expect(badges.map(b => b.label)).toEqual(['Highly rated instructor', 'Higher grades', 'Small lectures']);
    expect(badges[0].sources).toHaveLength(1);
    expect(badges[2].evidence).toContain('1 recorded lecture section');
  });
  it('uses released grades rather than projections, with the correct comparison', () => {
    expect(get()[1].evidence).toContain('Spring 2026');
    expect(get()[1].evidence).toContain('latest released grades before Fall 2026');
    expect(get({ scope: 'COMPSCI' })[1].label).toBe('Lower grades');
    expect(get({ term: '1252' }).some(b => b.id === 'grade-outcomes')).toBe(false);
  });
  it('does not carry past teachers or enrollment into a new term', () => {
    expect(get({ term: '1274' }).map(b => b.id)).toEqual(['grade-outcomes']);
    expect(get({ instructors: [{ ...instructors[0], terms: [{ term: '1264' }] }] }).some(b => b.id === 'rated-teacher')).toBe(false);
  });
  it('omits sparse and unavailable evidence without falling further back', () => {
    expect(get({ context: null }).map(b => b.id)).toEqual(['rated-teacher', 'lecture-size']);
    const sparse = structuredClone(context); sparse.terms['1264'].count = 29;
    expect(get({ context: sparse }).some(b => b.id === 'grade-outcomes')).toBe(false);
  });
  it('uses historical aggregate and latest roster when all terms are selected', () => {
    const all = { ...context, all: { gpa: 3.5, count: 500 }, benchmarks: { ...context.benchmarks, all: { school: { gpa: 3, size: 100 } } } };
    expect(get({ term: '', context: all }).map(b => b.id)).toHaveLength(3);
    expect(get({ term: '', context: all })[1].evidence).toContain('All recorded terms');
  });
});
