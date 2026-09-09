import { building, dev } from "$app/environment";
import { error } from "@sveltejs/kit";
import { drizzle } from "drizzle-orm/d1";
import { drizzle as proxy } from "drizzle-orm/sqlite-proxy";
import type { BaseSQLiteDatabase } from "drizzle-orm/sqlite-core";
import * as schema from "./schema";

let local: any;
export async function localDatabase() {
  if (!local) {
    const moduleName = "node:sqlite";
    const { DatabaseSync } = await import(/* @vite-ignore */ moduleName);
    local = new DatabaseSync(".site/site.sqlite", { readOnly: true });
  }
  return local;
}
const clients = new WeakMap<D1Database, ReturnType<typeof drizzle<typeof schema>>>();
const localClient = proxy(async (statement, params, method) => {
  if (method !== "all" && method !== "get" && method !== "values")
    throw new Error("The website database is read-only");
  const prepared = (await localDatabase()).prepare(statement);
  prepared.setReturnArrays(true);
  return { rows: method === "get" ? prepared.get(...params) : prepared.all(...params) };
}, { schema });
export function database(platform?: App.Platform): BaseSQLiteDatabase<"async", any, typeof schema> {
  if (building || dev) return localClient;
  const binding = platform?.env.DATA_SLOT === "b" ? platform.env.DB_B : platform?.env.DB_A;
  if (!binding) error(503, "Dataset database unavailable");
  let client = clients.get(binding);
  if (!client) { client = drizzle(binding, { schema }); clients.set(binding, client); }
  return client;
}
