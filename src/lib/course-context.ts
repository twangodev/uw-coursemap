export interface PeerCourse {
  uid: string;
  code: string;
  term: string;
  gpa: number;
  count: number;
  topShare: number;
  subjects: string[];
}

export function compareCourse(
  course: PeerCourse,
  peers: PeerCourse[],
  subject = "",
) {
  const cohort = peers.filter(
    (peer) =>
      peer.count >= 30 &&
      peer.term === course.term &&
      (!subject || peer.subjects.includes(subject)),
  );
  if (course.count < 30 || cohort.length < 10) return null;
  const others = cohort.filter((peer) => peer.uid !== course.uid);
  const counts = cohort.map((peer) => peer.count).sort((a, b) => a - b);
  const medianCount =
    (counts[Math.floor((counts.length - 1) / 2)] +
      counts[Math.floor(counts.length / 2)]) /
    2;
  return {
    size: cohort.length,
    gpaPercentile: Math.round(
      (100 * others.filter((peer) => peer.gpa < course.gpa).length) /
        others.length,
    ),
    countPercentile: Math.round(
      (100 * others.filter((peer) => peer.count < course.count).length) /
        others.length,
    ),
    medianCount,
    histogram: Array.from({ length: 10 }, (_, i) => ({
      range: `${(i * 0.4).toFixed(1)}–${((i + 1) * 0.4).toFixed(1)}`,
      count: cohort.filter(
        (peer) => Math.min(9, Math.floor(peer.gpa / 0.4)) === i,
      ).length,
      current: Math.min(9, Math.floor(course.gpa / 0.4)) === i,
    })),
  };
}
