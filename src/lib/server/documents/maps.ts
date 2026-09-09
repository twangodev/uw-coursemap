import type { DocumentContext } from "./types";
import { courseMap } from "$lib/server/course-map";
export async function maps({platform}: DocumentContext) { return {subject:null, graph:await courseMap(platform)}; }
