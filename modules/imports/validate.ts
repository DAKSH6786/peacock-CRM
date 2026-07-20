import type {
  DuplicatePolicy,
  ImportColumnDef,
  ImportEntityDefinition,
  PartialImportPolicy,
} from "./catalog";

export type ImportRow = Record<string, string>;

export type RowValidationError = {
  row: number;
  field?: string;
  code: string;
  message: string;
};

export type ValidatedImportRow = {
  rowNumber: number;
  data: ImportRow;
  errors: RowValidationError[];
  isDuplicate: boolean;
  duplicateOfRow?: number;
};

export type ImportValidationResult = {
  rows: ValidatedImportRow[];
  validCount: number;
  invalidCount: number;
  duplicateCount: number;
  errors: RowValidationError[];
  /** Whether the job may proceed under the selected partial policy */
  canCommit: boolean;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function cellValue(raw: unknown): string {
  if (raw == null) return "";
  return String(raw).trim();
}

export function parseCsv(text: string): { headers: string[]; rows: ImportRow[] } {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0);

  if (lines.length === 0) {
    return { headers: [], rows: [] };
  }

  const headers = splitCsvLine(lines[0]!).map((h) => h.trim());
  const rows = lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row: ImportRow = {};
    headers.forEach((header, index) => {
      row[header] = cellValue(cells[index]);
    });
    return row;
  });

  return { headers, rows };
}

/** Minimal CSV splitter supporting quoted fields */
export function splitCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]!;
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === "," && !inQuotes) {
      result.push(current);
      current = "";
      continue;
    }
    current += ch;
  }
  result.push(current);
  return result;
}

export function applyColumnMapping(
  rawRows: ImportRow[],
  mapping: Record<string, string>,
): ImportRow[] {
  return rawRows.map((raw) => {
    const mapped: ImportRow = {};
    for (const [targetField, sourceColumn] of Object.entries(mapping)) {
      if (!sourceColumn) continue;
      mapped[targetField] = cellValue(raw[sourceColumn]);
    }
    return mapped;
  });
}

function validateField(
  column: ImportColumnDef,
  value: string,
  rowNumber: number,
): RowValidationError | null {
  if (column.required && !value) {
    return {
      row: rowNumber,
      field: column.key,
      code: "REQUIRED",
      message: `${column.label} is required`,
    };
  }
  if (!value) return null;

  switch (column.type) {
    case "email":
      if (!EMAIL_RE.test(value)) {
        return {
          row: rowNumber,
          field: column.key,
          code: "INVALID_EMAIL",
          message: `${column.label} must be a valid email`,
        };
      }
      break;
    case "date":
      if (!DATE_RE.test(value) || Number.isNaN(Date.parse(value))) {
        return {
          row: rowNumber,
          field: column.key,
          code: "INVALID_DATE",
          message: `${column.label} must be YYYY-MM-DD`,
        };
      }
      break;
    case "number":
      if (Number.isNaN(Number(value))) {
        return {
          row: rowNumber,
          field: column.key,
          code: "INVALID_NUMBER",
          message: `${column.label} must be a number`,
        };
      }
      break;
    case "boolean":
      if (!["true", "false", "1", "0", "yes", "no"].includes(value.toLowerCase())) {
        return {
          row: rowNumber,
          field: column.key,
          code: "INVALID_BOOLEAN",
          message: `${column.label} must be true/false`,
        };
      }
      break;
    default:
      break;
  }
  return null;
}

function uniqueFingerprint(
  definition: ImportEntityDefinition,
  row: ImportRow,
): string | null {
  const parts = definition.uniqueKeys.map((key) => cellValue(row[key]).toLowerCase());
  if (parts.every((p) => !p)) return null;
  return parts.join("|");
}

export function validateImportRows(
  definition: ImportEntityDefinition,
  rows: ImportRow[],
  options?: {
    duplicatePolicy?: DuplicatePolicy;
    partialPolicy?: PartialImportPolicy;
    /** Existing unique fingerprints already in the system */
    existingKeys?: Set<string>;
  },
): ImportValidationResult {
  const duplicatePolicy = options?.duplicatePolicy ?? "SKIP";
  const partialPolicy = options?.partialPolicy ?? "COMMIT_VALID";
  const existingKeys = options?.existingKeys ?? new Set<string>();

  const seen = new Map<string, number>();
  const validated: ValidatedImportRow[] = [];
  const allErrors: RowValidationError[] = [];

  rows.forEach((row, index) => {
    const rowNumber = index + 2; // header is row 1
    const errors: RowValidationError[] = [];

    for (const column of definition.columns) {
      const err = validateField(column, cellValue(row[column.key]), rowNumber);
      if (err) errors.push(err);
    }

    let isDuplicate = false;
    let duplicateOfRow: number | undefined;
    const fingerprint = uniqueFingerprint(definition, row);

    if (fingerprint) {
      if (existingKeys.has(fingerprint)) {
        isDuplicate = true;
        errors.push({
          row: rowNumber,
          code: "DUPLICATE_EXISTING",
          message: `Row matches an existing ${definition.label} record`,
        });
      } else if (seen.has(fingerprint)) {
        isDuplicate = true;
        duplicateOfRow = seen.get(fingerprint);
        errors.push({
          row: rowNumber,
          code: "DUPLICATE_IN_FILE",
          message: `Duplicate of row ${duplicateOfRow} in this file`,
        });
      } else {
        seen.set(fingerprint, rowNumber);
      }
    }

    if (isDuplicate && duplicatePolicy === "FAIL") {
      // already recorded
    } else if (isDuplicate && duplicatePolicy === "SKIP") {
      // keep as duplicate; caller will skip
    } else if (isDuplicate && duplicatePolicy === "UPDATE") {
      // allow through as valid duplicate update candidate — strip duplicate error for commit path
      const filtered = errors.filter(
        (e) => e.code !== "DUPLICATE_EXISTING" && e.code !== "DUPLICATE_IN_FILE",
      );
      errors.length = 0;
      errors.push(...filtered);
    }

    allErrors.push(...errors);
    validated.push({
      rowNumber,
      data: row,
      errors,
      isDuplicate,
      duplicateOfRow,
    });
  });

  const invalidCount = validated.filter((r) => r.errors.length > 0).length;
  const duplicateCount = validated.filter((r) => r.isDuplicate).length;
  const validCount = validated.length - invalidCount;

  const canCommit =
    partialPolicy === "COMMIT_VALID"
      ? validCount > 0 || (duplicatePolicy === "SKIP" && validated.length > 0)
      : invalidCount === 0;

  return {
    rows: validated,
    validCount,
    invalidCount,
    duplicateCount,
    errors: allErrors,
    canCommit,
  };
}

export function buildErrorCsv(
  definition: ImportEntityDefinition,
  result: ImportValidationResult,
): string {
  const headers = ["row", "field", "code", "message", ...definition.columns.map((c) => c.key)];
  const lines = [headers.join(",")];

  for (const row of result.rows) {
    if (row.errors.length === 0) continue;
    for (const err of row.errors) {
      const values = [
        String(err.row),
        err.field ?? "",
        err.code,
        `"${err.message.replace(/"/g, '""')}"`,
        ...definition.columns.map((c) => {
          const v = row.data[c.key] ?? "";
          return v.includes(",") ? `"${v.replace(/"/g, '""')}"` : v;
        }),
      ];
      lines.push(values.join(","));
    }
  }

  return `${lines.join("\n")}\n`;
}

export function previewRows(
  rows: ImportRow[],
  limit = 20,
): ImportRow[] {
  return rows.slice(0, limit);
}
