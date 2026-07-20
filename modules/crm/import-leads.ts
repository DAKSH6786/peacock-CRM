import "server-only";

import { prisma } from "@/database";
import {
  normalizeCompanyName,
  normalizeDomain,
  normalizeEmail,
  normalizePhone,
} from "@/modules/crm/normalize";
import { refreshDuplicateCandidates, computeAndPersistLeadScore } from "@/modules/crm/leads";

export async function createLeadFromImportRow(input: {
  organizationId: string;
  createdById?: string | null;
  row: Record<string, string>;
}) {
  const pipeline = await prisma.pipeline.findFirst({
    where: { organizationId: input.organizationId, deletedAt: null },
    orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
    include: {
      stages: {
        where: { deletedAt: null },
        orderBy: { sortOrder: "asc" },
        take: 1,
      },
    },
  });
  const status = await prisma.leadStatus.findFirst({
    where: { organizationId: input.organizationId, deletedAt: null },
    orderBy: { sortOrder: "asc" },
  });
  const source = input.row.source
    ? await prisma.leadSource.findFirst({
        where: {
          organizationId: input.organizationId,
          OR: [
            { name: { equals: input.row.source, mode: "insensitive" } },
            { code: { equals: input.row.source, mode: "insensitive" } },
          ],
          deletedAt: null,
        },
      })
    : null;

  const lead = await prisma.lead.create({
    data: {
      organizationId: input.organizationId,
      personName: input.row.fullName || "Unknown",
      companyName: input.row.company || null,
      email: input.row.email || null,
      phone: input.row.phone || null,
      sourceId: source?.id ?? null,
      statusId: status?.id ?? null,
      pipelineId: pipeline?.id ?? null,
      stageId: pipeline?.stages[0]?.id ?? null,
      probability: pipeline?.stages[0]?.probability ?? null,
      normalizedEmail: normalizeEmail(input.row.email),
      normalizedPhone: normalizePhone(input.row.phone),
      normalizedCompany: normalizeCompanyName(input.row.company),
      normalizedDomain: normalizeDomain(input.row.email),
      createdById: input.createdById ?? null,
      interestedServices: [],
    },
  });

  await computeAndPersistLeadScore(lead.id);
  await refreshDuplicateCandidates(input.organizationId, lead.id);
  return lead;
}
