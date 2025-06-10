export type GradeData = {
  total: number;
  a: number;
  ab: number;
  b: number;
  bc: number;
  c: number;
  d: number;
  f: number;
  satisfactory: number;
  unsatisfactory: number;
  credit: number;
  no_credit: number;
  passed: number;
  incomplete: number;
  no_work: number;
  not_reported: number;
  other: number;
  instructors?: string[] | null;
};

export function getTotalOtherGrades(gradeData: GradeData): number {
  return (
    gradeData.satisfactory +
    gradeData.unsatisfactory +
    gradeData.credit +
    gradeData.no_credit +
    gradeData.passed +
    gradeData.incomplete +
    gradeData.no_work +
    gradeData.not_reported +
    gradeData.other
  );
}

export function calculateGradePointAverage(
  gradeData: GradeData | undefined | null,
): number | null {
  if (!gradeData || gradeData.total === 0) {
    return null;
  }
  let totalPoints =
    gradeData.a * 4 +
    gradeData.ab * 3.5 +
    gradeData.b * 3 +
    gradeData.bc * 2.5 +
    gradeData.c * 2 +
    gradeData.d;
  return totalPoints / gradeData.total;
}

export function calculateCompletionRate(
  gradeData: GradeData | undefined | null,
): number | null {
  if (!gradeData || gradeData.total === 0) {
    return null;
  }
  let totalCompletions =
    gradeData.a +
    gradeData.ab +
    gradeData.b +
    gradeData.bc +
    gradeData.c +
    gradeData.passed +
    gradeData.satisfactory +
    gradeData.credit;
  return (totalCompletions * 100) / gradeData.total;
}

export function calculateARate(
  gradeData: GradeData | undefined | null,
): number | null {
  if (!gradeData || gradeData.total === 0) {
    return null;
  }
  let totalAs = gradeData.a;
  return (totalAs * 100) / gradeData.total;
}
