import { expect, it } from "vitest";
import { departmentName, departmentLabel } from "../../src/lib/departments";
import entries from "../../.site/entries.json";
it("has an official full name for every imported department", () => {
  expect(departmentName("COMPSCI")).toBe("Computer Sciences");
  expect(departmentLabel("ECE")).toBe(
    "Electrical and Computer Engineering (ECE)",
  );
  expect(departmentName("UNKNOWN")).toBe("UNKNOWN");
  for (const subject of entries.subjects)
    expect(departmentName(subject)).not.toBe(subject);
});
