export interface Meeting {
  meeting_id: string;
  course_id?: string;
  name: string;
  starts_at: string;
  ends_at: string;
  building?: string;
  room?: string;
  instructor_names?: string[];
}
const formatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Chicago",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
export function localTime(value: string) {
  const parts = Object.fromEntries(
    formatter
      .formatToParts(new Date(value.replace(" ", "T")))
      .map((p) => [p.type, p.value]),
  );
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    minute: Number(parts.hour) * 60 + Number(parts.minute),
  };
}
export function addDays(day: string, n: number) {
  const d = new Date(day + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
export function monday(day: string) {
  const d = new Date(day + "T12:00:00Z").getUTCDay();
  return addDays(day, -((d + 6) % 7));
}
export function sectionName(name: string) {
  return name.replace(/\s*#\d+\s*$/, "");
}
export function timeLabel(minute: number) {
  return `${Math.floor(minute / 60) % 12 || 12}${minute % 60 ? ":" + String(minute % 60).padStart(2, "0") : ""}${minute < 720 ? "am" : "pm"}`;
}
export function dayLabel(day: string) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
  }).format(new Date(day + "T12:00:00Z"));
}
export function placeMeetings(meetings: Meeting[], day: string) {
  const rows = meetings
    .map((m) => ({
      meeting: m,
      start: localTime(m.starts_at),
      end: localTime(m.ends_at),
    }))
    .filter((m) => m.start.date === day)
    .sort((a, b) => a.start.minute - b.start.minute);
  const result: {
    meeting: Meeting;
    start: number;
    end: number;
    lane: number;
    lanes: number;
  }[] = [];
  let cluster: typeof result = [],
    ends: number[] = [],
    clusterEnd = 0;
  const flush = () => {
    for (const event of cluster) event.lanes = ends.length;
    cluster = [];
    ends = [];
  };
  for (const row of rows) {
    const start = row.start.minute,
      end = row.end.date === day ? row.end.minute : 1440;
    if (start >= clusterEnd) flush();
    let lane = ends.findIndex((e) => e <= start);
    if (lane < 0) lane = ends.length;
    ends[lane] = end;
    clusterEnd = Math.max(start >= clusterEnd ? 0 : clusterEnd, end);
    const event = { meeting: row.meeting, start, end, lane, lanes: 1 };
    cluster.push(event);
    result.push(event);
  }
  flush();
  return result;
}
