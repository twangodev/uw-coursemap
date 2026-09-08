import { building, dev } from "$app/environment";
import { error } from "@sveltejs/kit";
import { normalize } from "$lib/format";
import type { Status } from "$lib/types";
let local: any;
export async function query<T = any>(
  platform: App.Platform | undefined,
  sql: string,
  values: unknown[] = [],
): Promise<T[]> {
  if (!building && !dev) {
    const database =
      platform?.env.DATA_SLOT === "green"
        ? platform.env.DB_GREEN
        : platform?.env.DB_BLUE;
    if (!database) error(503, "Dataset database unavailable");
    const result = await database
      .prepare(sql)
      .bind(...values)
      .all<T>();
    return result.results;
  }
  if (!local) {
    const moduleName = "node:sqlite";
    const { DatabaseSync } = await import(/* @vite-ignore */ moduleName);
    local = new DatabaseSync(".site/site.sqlite", { readOnly: true });
  }
  return local.prepare(sql).all(...values) as T[];
}
export async function status(platform?: App.Platform): Promise<Status> {
  const [r] = await query(
    platform,
    "SELECT value FROM metadata WHERE key='status'",
  );
  if (!r) error(503, "Dataset not imported");
  return {
    ...JSON.parse(r.value),
    deployed_at: building || dev ? null : platform?.env.DEPLOYED_AT || null,
    slot: building || dev ? null : platform?.env.DATA_SLOT || null,
  };
}
export async function pageData(
  kind: string,
  uid: string,
  platform?: App.Platform,
): Promise<any> {
  const table = kind === "courses" ? "courses" : "instructors";
  const [r] = await query(
    platform,
    `SELECT payload FROM ${table} WHERE uid=?`,
    [uid],
  );
  if (!r)
    error(
      404,
      kind === "courses" ? "Course not found" : "Instructor not found",
    );
  return JSON.parse(r.payload);
}
export async function assertRevision(url: URL, platform?: App.Platform) {
  const s = await status(platform);
  if (
    url.searchParams.has("revision") &&
    url.searchParams.get("revision") !== s.revision
  )
    error(409, "Dataset updated. Reload this page to continue.");
  return s;
}
export function pageNumber(url: URL) {
  const n = Number(url.searchParams.get("page") || 1);
  if (!Number.isInteger(n) || n < 1 || n > 10000) error(400, "Invalid page");
  return n;
}
export async function search(url: URL, platform?: App.Platform) {
  const q = (url.searchParams.get("q") || "").trim();
  if (q.length > 200) error(400, "Query is too long");
  const kind =
    url.searchParams.get("kind") === "instructor" ? "instructor" : "course";
  const searchable =
    kind === "course"
      ? q.replace(/\bCOMP\s+SCI\b/gi, "COMPSCI").replace(/\bCS\b/gi, "COMPSCI")
      : q;
  const tokens = searchable.match(/[\p{L}\p{N}]+/gu) || [];
  const expression = tokens.map((t) => '"' + t + '"*').join(" AND ");
  const page = pageNumber(url),
    values: unknown[] = [];
  let from = kind === "course" ? "courses c" : "instructors c";
  let where = "1=1";
  if (expression) {
    from += ` JOIN (SELECT uid,bm25(search,0,0,12,6,1) score FROM search WHERE search MATCH ? AND kind=? ${kind === "course" ? "UNION ALL SELECT uid,-1000000 score FROM aliases WHERE alias=?" : ""}) m ON m.uid=c.uid`;
    values.push(expression, kind);
    if (kind === "course") values.push(normalize(q));
  }
  if (kind === "course") {
    for (const [param, clause] of [
      [
        "subject",
        "EXISTS(SELECT 1 FROM subjects s WHERE s.uid=c.uid AND s.subject=?)",
      ],
      [
        "instructor",
        "EXISTS(SELECT 1 FROM teaching t WHERE t.course_uid=c.uid AND t.instructor_uid=?)",
      ],
      [
        "term",
        "(EXISTS(SELECT 1 FROM teaching t WHERE t.course_uid=c.uid AND t.term=?) OR EXISTS(SELECT 1 FROM grades g WHERE g.uid=c.uid AND g.term=?))",
      ],
    ]) {
      const v = url.searchParams.get(param);
      if (v) {
        where += " AND " + clause;
        values.push(v);
        if (param === "term") values.push(v);
      }
    }
    for (const [param, col, op] of [
      ["credits_min", "credits_max", ">="],
      ["credits_max", "credits_min", "<="],
      ["gpa_min", "gpa", ">="],
    ]) {
      const v = url.searchParams.get(param);
      if (v) {
        const n = Number(v);
        if (!Number.isFinite(n)) error(400, "Invalid numeric filter");
        where += ` AND c.${col}${op}?`;
        values.push(n);
      }
    }
  }
  const sort = url.searchParams.get("sort");
  const order =
    kind === "instructor"
      ? "c.current DESC,c.name"
      : sort === "gpa"
        ? "c.gpa DESC,c.code"
        : expression
          ? "min(m.score),c.code"
          : "c.code";
  const fields =
    kind === "course"
      ? "c.uid course_uid,c.code course_id,c.title,c.credits_min,c.credits_max,c.gpa"
      : "c.uid instructor_uid,c.name,c.current";
  const [count] = await query(
    platform,
    `SELECT count(DISTINCT c.uid) total FROM ${from} WHERE ${where}`,
    values,
  );
  const items = await query(
    platform,
    `SELECT ${fields} FROM ${from} WHERE ${where} GROUP BY c.uid ORDER BY ${order} LIMIT 30 OFFSET ?`,
    [...values, (page - 1) * 30],
  );
  return { items, total: count.total, page, kind, q };
}
export async function gradeRows(
  uid: string,
  url: URL,
  platform?: App.Platform,
) {
  const values: unknown[] = [uid];
  let where = "uid=?";
  const instructor = url.searchParams.get("instructor");
  if (instructor) {
    where +=
      " AND section<>'' AND EXISTS(SELECT 1 FROM json_each(grades.instructors) WHERE value=?)";
    values.push(instructor);
  } else where += " AND section=''";
  const term = url.searchParams.get("term");
  if (term) {
    where += " AND term=?";
    values.push(term);
  }
  const page = pageNumber(url);
  const [count] = await query(
    platform,
    `SELECT count(*) total FROM grades WHERE ${where}`,
    values,
  );
  const data = await query(
    platform,
    `SELECT payload FROM grades WHERE ${where} ORDER BY term DESC,section LIMIT 100 OFFSET ?`,
    [...values, (page - 1) * 100],
  );
  return {
    items: data.map((r) => JSON.parse(r.payload)),
    total: count.total,
    page,
  };
}
