import { sqliteTable, text, real, integer } from "drizzle-orm/sqlite-core";
// Read model owned by the HF importer; migrations remain part of that import.
export const metadata = sqliteTable("metadata", {
  key: text("key").primaryKey(), value: text("value").notNull(),
});
export const courses = sqliteTable("courses", {
  uid: text("uid").primaryKey(), code: text("code"), title: text("title"),
  description: text("description"), creditsMin: real("credits_min"),
  creditsMax: real("credits_max"), gpa: real("gpa"), payload: text("payload").notNull(),
});
export const instructors = sqliteTable("instructors", {
  uid: text("uid").primaryKey(), name: text("name"), current: integer("current"),
  payload: text("payload").notNull(),
});
