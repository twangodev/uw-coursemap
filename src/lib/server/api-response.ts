import { json } from "@sveltejs/kit";
import type { z } from "zod";
/** Validate the JSON wire representation (undefined object properties are omitted). */
export function apiJson<T extends z.ZodType>(
  schema: T,
  data: unknown,
  init?: ResponseInit,
) {
  return json(schema.parse(JSON.parse(JSON.stringify(data))), init);
}
