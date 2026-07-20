import { describe, expect, it } from "vitest";

import {
  applyColumnMapping,
  parseCsv,
  validateImportRows,
} from "@/modules/imports/validate";
import { getImportDefinition } from "@/modules/imports/catalog";
import { prepareImport, suggestColumnMapping } from "@/modules/imports/prepare";

describe("import validation", () => {
  const leads = getImportDefinition("leads")!;

  it("parses csv and suggests column mapping", () => {
    const csv = "fullName,email,company\nAda Lovelace,ada@example.com,Analytical\n";
    const parsed = parseCsv(csv);
    expect(parsed.headers).toEqual(["fullName", "email", "company"]);
    expect(parsed.rows).toHaveLength(1);

    const mapping = suggestColumnMapping(parsed.headers, "leads");
    expect(mapping.fullName).toBe("fullName");
    expect(mapping.email).toBe("email");
  });

  it("flags required and email errors", () => {
    const rows = applyColumnMapping(
      [{ full_name: "No Email", email: "bad", company: "X" }],
      { fullName: "full_name", email: "email", company: "company" },
    );
    const result = validateImportRows(leads, rows);
    expect(result.invalidCount).toBe(1);
    expect(result.errors.some((e) => e.code === "INVALID_EMAIL")).toBe(true);
  });

  it("detects in-file duplicates", () => {
    const result = validateImportRows(
      leads,
      [
        { fullName: "A", email: "a@example.com" },
        { fullName: "A2", email: "a@example.com" },
      ],
      { duplicatePolicy: "FAIL" },
    );
    expect(result.duplicateCount).toBe(1);
    expect(result.errors.some((e) => e.code === "DUPLICATE_IN_FILE")).toBe(true);
  });

  it("honours ALL_OR_NOTHING partial policy", () => {
    const prepared = prepareImport({
      entityType: "leads",
      csvText: "fullName,email\nGood,good@example.com\nBad,not-an-email\n",
      columnMapping: { fullName: "fullName", email: "email" },
      partialPolicy: "ALL_OR_NOTHING",
    });
    expect(prepared.validation.canCommit).toBe(false);
  });

  it("allows COMMIT_VALID when some rows are good", () => {
    const prepared = prepareImport({
      entityType: "vendors",
      csvText: "name,email\nAcme,ok@example.com\n,bad\n",
      columnMapping: { name: "name", email: "email" },
      partialPolicy: "COMMIT_VALID",
    });
    expect(prepared.validation.validCount).toBe(1);
    expect(prepared.validation.canCommit).toBe(true);
  });
});
