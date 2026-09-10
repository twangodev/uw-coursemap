import type { DocumentContext } from "./types";
import campus from "../../../../.site/import/campus.json";
import { query } from "$lib/server/data";
export async function home({ platform }: DocumentContext) {
  return {
    campus: { ...campus, timezone: "America/Chicago" as const },
    courses: await query(
      platform,
      "SELECT uid course_uid,code course_id,title,credits_min,credits_max,gpa FROM courses WHERE uid IN (SELECT uid FROM aliases WHERE alias IN ('COMPSCI300','COMPSCI400','COMPSCI759')) ORDER BY code",
    ),
  };
}
