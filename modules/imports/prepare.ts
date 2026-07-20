import type { MembershipRole } from "@prisma/client";

import type { Permission, SessionUser } from "@/permissions/types";
import { hasPermission } from "@/permissions/types";

import {
  getImportDefinition,
  type DuplicatePolicy,
  type ImportEntityType,
  type PartialImportPolicy,
} from "./catalog";
import {
  applyColumnMapping,
  buildErrorCsv,
  parseCsv,
  previewRows,
  validateImportRows,
  type ImportRow,
  type ImportValidationResult,
} from "./validate";

export function canImportEntity(
  user: SessionUser,
  entityType: string,
): boolean {
  const definition = getImportDefinition(entityType);
  if (!definition) return false;
  return hasPermission(user.role as MembershipRole | null, definition.permission);
}

export type PrepareImportInput = {
  entityType: ImportEntityType;
  csvText: string;
  columnMapping: Record<string, string>;
  duplicatePolicy?: DuplicatePolicy;
  partialPolicy?: PartialImportPolicy;
  existingKeys?: Set<string>;
};

export type PreparedImport = {
  entityType: ImportEntityType;
  headers: string[];
  mappedRows: ImportRow[];
  preview: ImportRow[];
  validation: ImportValidationResult;
  errorCsv: string;
};

export function prepareImport(input: PrepareImportInput): PreparedImport {
  const definition = getImportDefinition(input.entityType);
  if (!definition) {
    throw new Error(`Unknown import entity: ${input.entityType}`);
  }

  const parsed = parseCsv(input.csvText);
  const mappedRows = applyColumnMapping(parsed.rows, input.columnMapping);
  const validation = validateImportRows(definition, mappedRows, {
    duplicatePolicy: input.duplicatePolicy,
    partialPolicy: input.partialPolicy,
    existingKeys: input.existingKeys,
  });

  return {
    entityType: input.entityType,
    headers: parsed.headers,
    mappedRows,
    preview: previewRows(mappedRows),
    validation,
    errorCsv: buildErrorCsv(definition, validation),
  };
}

export function suggestColumnMapping(
  headers: string[],
  entityType: ImportEntityType,
): Record<string, string> {
  const definition = getImportDefinition(entityType);
  if (!definition) return {};

  const normalized = new Map(
    headers.map((h) => [h.trim().toLowerCase().replace(/[\s_]+/g, ""), h]),
  );

  const mapping: Record<string, string> = {};
  for (const column of definition.columns) {
    const key = column.key.toLowerCase().replace(/[\s_]+/g, "");
    const label = column.label.toLowerCase().replace(/[\s_]+/g, "");
    const match = normalized.get(key) ?? normalized.get(label);
    if (match) mapping[column.key] = match;
  }
  return mapping;
}

export function permissionForImport(entityType: string): Permission | null {
  return getImportDefinition(entityType)?.permission ?? null;
}
