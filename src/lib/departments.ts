import catalog from "./data/department-names.json";
/** Official UW Guide subject names; codes remain the stable routing/data keys. */
export function departmentName(code: string) {
  return (catalog.names as Record<string, string>)[code] || code;
}
export function departmentLabel(code: string) {
  const name = departmentName(code);
  return name === code ? code : `${name} (${code})`;
}
