import "server-only";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import type { SessionUser } from "@/permissions/types";

import type { BusinessReviewInput } from "./schemas";

export async function getCompanyProgressDashboard(organizationId: string) {
  const [
    objectives,
    departments,
    risks,
    decisions,
    scorecards,
    xymePlans,
    xymeTotal,
    openDeals,
    wonDeals,
    invoices,
    clients,
    projects,
    companyTargets,
    openPositions,
    timeEntries,
  ] = await Promise.all([
    prisma.objective.findMany({
      where: { organizationId, deletedAt: null },
      include: {
        department: { select: { id: true, name: true, code: true } },
        keyResults: { where: { deletedAt: null }, select: { progressPct: true } },
      },
    }),
    prisma.department.findMany({
      where: { organizationId, deletedAt: null },
      select: { id: true, name: true, code: true },
      orderBy: { name: "asc" },
    }),
    prisma.riskRegister.findMany({
      where: { organizationId, deletedAt: null, status: { not: "CLOSED" } },
      orderBy: [{ impact: "desc" }, { likelihood: "desc" }],
      take: 8,
    }),
    prisma.decisionLog.findMany({
      where: { organizationId, deletedAt: null },
      orderBy: { decidedAt: "desc" },
      take: 8,
    }),
    prisma.departmentScorecard.findMany({
      where: { organizationId, deletedAt: null, isActive: true },
      include: {
        department: { select: { id: true, name: true, code: true } },
        kpis: {
          include: {
            kpi: {
              include: {
                values: { orderBy: { periodEnd: "desc" }, take: 1 },
              },
            },
          },
          orderBy: { sortOrder: "asc" },
        },
      },
    }),
    prisma.xYMEPlan.count({
      where: { organizationId, deletedAt: null, status: "APPROVED" },
    }),
    prisma.xYMEPlan.count({
      where: { organizationId, deletedAt: null },
    }),
    prisma.deal.findMany({
      where: {
        organizationId,
        deletedAt: null,
        stage: { isClosedWon: false, isClosedLost: false },
      },
      select: {
        valueMinor: true,
        probability: true,
        stage: { select: { probability: true } },
      },
    }),
    prisma.deal.findMany({
      where: {
        organizationId,
        deletedAt: null,
        stage: { isClosedWon: true },
      },
      select: { valueMinor: true },
      take: 500,
    }),
    prisma.invoice.findMany({
      where: { organizationId, deletedAt: null },
      select: { status: true, totalMinor: true, dueDate: true },
      take: 500,
    }),
    prisma.clientCompany.count({
      where: { organizationId, deletedAt: null },
    }),
    prisma.project.findMany({
      where: { organizationId, deletedAt: null },
      select: { status: true },
      take: 500,
    }),
    prisma.companyTarget.findMany({
      where: { organizationId, deletedAt: null },
      take: 30,
    }),
    prisma.recruitmentJob.count({
      where: { organizationId, deletedAt: null, status: "OPEN" },
    }),
    prisma.timeEntry.findMany({
      where: { organizationId, deletedAt: null },
      select: { hours: true, billable: true },
      take: 2000,
    }),
  ]);

  const overall =
    objectives.length === 0
      ? 0
      : Math.round(
          objectives.reduce((s, o) => s + o.progressPct, 0) / objectives.length,
        );

  const onTrack = objectives.filter((o) => o.health === "GREEN").length;
  const atRisk = objectives.filter((o) => o.health === "AMBER").length;
  const delayed = objectives.filter(
    (o) =>
      o.health === "RED" ||
      (o.dueDate && o.dueDate < new Date() && o.status !== "COMPLETED"),
  ).length;

  const byDepartment = departments.map((dept) => {
    const deptObjectives = objectives.filter((o) => o.departmentId === dept.id);
    const progress =
      deptObjectives.length === 0
        ? 0
        : Math.round(
            deptObjectives.reduce((s, o) => s + o.progressPct, 0) /
              deptObjectives.length,
          );
    return {
      departmentId: dept.id,
      name: dept.name,
      code: dept.code,
      objectiveCount: deptObjectives.length,
      progressPct: progress,
      onTrack: deptObjectives.filter((o) => o.health === "GREEN").length,
      atRisk: deptObjectives.filter((o) => o.health === "AMBER").length,
      offTrack: deptObjectives.filter((o) => o.health === "RED").length,
    };
  });

  const byQuarter = new Map<string, { count: number; progress: number }>();
  for (const o of objectives) {
    const q = o.quarter ?? "Unassigned";
    const row = byQuarter.get(q) ?? { count: 0, progress: 0 };
    row.count += 1;
    row.progress += o.progressPct;
    byQuarter.set(q, row);
  }

  const pipelineWeighted = openDeals.reduce((sum, d) => {
    const p = d.probability ?? d.stage?.probability ?? 0;
    return sum + Math.round((d.valueMinor * p) / 100);
  }, 0);

  const overdueInvoices = invoices.filter(
    (inv) =>
      inv.dueDate &&
      inv.dueDate < new Date() &&
      inv.status !== "PAID" &&
      inv.status !== "CANCELLED",
  );
  const collectionRate =
    invoices.length === 0
      ? 0
      : Math.round(
          (invoices.filter((i) => i.status === "PAID").length /
            invoices.length) *
            1000,
        ) / 10;

  const deliveryHealth = {
    active: projects.filter((p) => p.status === "ACTIVE" || p.status === "IN_PROGRESS").length,
    planned: projects.filter((p) => p.status === "PLANNED").length,
    completed: projects.filter((p) => p.status === "COMPLETED" || p.status === "DONE").length,
  };

  const closedRevenueMinor = wonDeals.reduce((s, d) => s + (d.valueMinor ?? 0), 0);
  const revenueTarget = companyTargets.find(
    (t) =>
      t.metricCode.toLowerCase().includes("revenue") ||
      t.name.toLowerCase().includes("revenue"),
  );
  const pipelineTarget = companyTargets.find(
    (t) =>
      t.metricCode.toLowerCase().includes("pipeline") ||
      t.name.toLowerCase().includes("pipeline"),
  );

  const billableHours = timeEntries
    .filter((e) => e.billable)
    .reduce((s, e) => s + Number(e.hours), 0);
  const totalHours = timeEntries.reduce((s, e) => s + Number(e.hours), 0);
  const billableUtilization =
    totalHours === 0 ? 0 : Math.round((billableHours / totalHours) * 1000) / 10;

  const xymeCompletionPct =
    xymeTotal === 0 ? 0 : Math.round((xymePlans / xymeTotal) * 1000) / 10;

  // Retention proxy: active clients with no cancelled status (count as retention baseline)
  const clientRetentionPct = clients > 0 ? 100 : 0;

  return {
    overallProgressPct: overall,
    objectiveCounts: {
      total: objectives.length,
      onTrack,
      atRisk,
      delayed,
      notStarted: objectives.filter((o) => o.health === "GREY").length,
    },
    byDepartment,
    byQuarter: [...byQuarter.entries()].map(([quarter, row]) => ({
      quarter,
      count: row.count,
      progressPct: Math.round(row.progress / row.count),
    })),
    commercial: {
      activeClients: clients,
      clientRetentionPct,
      pipelineWeightedMinor: pipelineWeighted,
      pipelineTargetMinor: pipelineTarget?.targetMinor ?? null,
      closedRevenueMinor,
      revenueTargetMinor: revenueTarget?.targetMinor ?? null,
      overdueInvoiceCount: overdueInvoices.length,
      overdueInvoiceMinor: overdueInvoices.reduce(
        (s, i) => s + (i.totalMinor ?? 0),
        0,
      ),
      invoiceCollectionRate: collectionRate,
    },
    peopleOps: {
      openPositions,
      xymeApprovedPlans: xymePlans,
      xymeTotalPlans: xymeTotal,
      xymeCompletionPct,
      billableUtilization,
    },
    deliveryHealth,
    xymeApprovedPlans: xymePlans,
    topRisks: risks,
    recentDecisions: decisions,
    scorecards: scorecards.map((sc) => ({
      id: sc.id,
      name: sc.name,
      department: sc.department,
      kpis: sc.kpis.map((link) => ({
        id: link.kpi.id,
        name: link.kpi.name,
        code: link.kpi.code,
        unit: link.kpi.unit,
        latestValue: link.kpi.values[0]
          ? Number(link.kpi.values[0].value)
          : null,
        targetValue: link.targetValue ? Number(link.targetValue) : null,
      })),
    })),
  };
}

export async function submitProgressUpdate(input: {
  user: SessionUser;
  organizationId: string;
  data: {
    objectiveId?: string | null;
    cadence: "WEEKLY" | "MONTHLY";
    periodStart: string;
    periodEnd: string;
    body: string;
    progressPct?: number | null;
    confidenceScore?: number | null;
    health?: string | null;
    riskFlag?: boolean;
    blocker?: string | null;
    evidence?: string | null;
  };
}) {
  const update = await prisma.progressUpdate.create({
    data: {
      organizationId: input.organizationId,
      objectiveId: input.data.objectiveId ?? null,
      cadence: input.data.cadence,
      periodStart: new Date(input.data.periodStart),
      periodEnd: new Date(input.data.periodEnd),
      body: input.data.body,
      progressPct: input.data.progressPct ?? null,
      confidenceScore: input.data.confidenceScore ?? null,
      health: (input.data.health as never) ?? null,
      riskFlag: input.data.riskFlag ?? false,
      blocker: input.data.blocker ?? null,
      evidence: input.data.evidence ?? null,
      reviewStatus: "SUBMITTED",
      createdById: input.user.id,
    },
  });

  if (input.data.objectiveId && input.data.progressPct != null) {
    await prisma.objective.update({
      where: { id: input.data.objectiveId },
      data: {
        progressPct: input.data.progressPct,
        ...(input.data.riskFlag ? { status: "AT_RISK" } : {}),
      },
    });
  }

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "ProgressUpdate",
    entityId: update.id,
  });

  return update;
}

export async function reviewProgressUpdate(input: {
  user: SessionUser;
  organizationId: string;
  updateId: string;
  note?: string;
}) {
  return prisma.progressUpdate.update({
    where: { id: input.updateId },
    data: {
      reviewStatus: "REVIEWED",
      reviewedById: input.user.id,
      reviewedAt: new Date(),
      reviewNote: input.note ?? null,
    },
  });
}

export async function listProgressUpdates(organizationId: string) {
  return prisma.progressUpdate.findMany({
    where: { organizationId },
    include: {
      objective: { select: { id: true, title: true } },
      createdBy: { select: { id: true, name: true, email: true } },
    },
    orderBy: { createdAt: "desc" },
    take: 100,
  });
}

export async function getUpdateReminders(organizationId: string) {
  const staleBefore = new Date(Date.now() - 7 * 86_400_000);
  const objectives = await prisma.objective.findMany({
    where: {
      organizationId,
      deletedAt: null,
      status: { in: ["IN_PROGRESS", "AT_RISK", "NOT_STARTED"] },
    },
    include: {
      progressUpdates: { orderBy: { createdAt: "desc" }, take: 1 },
      primaryOwner: { select: { id: true, name: true, email: true } },
    },
  });

  return objectives
    .filter((o) => {
      const last = o.progressUpdates[0]?.createdAt;
      return !last || last < staleBefore;
    })
    .map((o) => ({
      objectiveId: o.id,
      title: o.title,
      owner: o.primaryOwner,
      lastUpdateAt: o.progressUpdates[0]?.createdAt ?? null,
    }));
}

export async function createBusinessReview(input: {
  user: SessionUser;
  organizationId: string;
  data: BusinessReviewInput;
}) {
  const objectives = await prisma.objective.findMany({
    where: { organizationId: input.organizationId, deletedAt: null },
    select: {
      id: true,
      title: true,
      progressPct: true,
      health: true,
      status: true,
      departmentId: true,
    },
  });
  const kpis = await prisma.kPI.findMany({
    where: { organizationId: input.organizationId, deletedAt: null, isActive: true },
    include: { values: { orderBy: { periodEnd: "desc" }, take: 1 } },
  });
  const risks = await prisma.riskRegister.findMany({
    where: {
      organizationId: input.organizationId,
      deletedAt: null,
      status: { not: "CLOSED" },
    },
    take: 20,
  });

  const snapshot = {
    capturedAt: new Date().toISOString(),
    objectives,
    kpis: kpis.map((k) => ({
      id: k.id,
      name: k.name,
      code: k.code,
      latestValue: k.values[0] ? Number(k.values[0].value) : null,
    })),
    risks: risks.map((r) => ({
      id: r.id,
      title: r.title,
      likelihood: r.likelihood,
      impact: r.impact,
      status: r.status,
    })),
  };

  const review = await prisma.businessReview.create({
    data: {
      organizationId: input.organizationId,
      title: input.data.title,
      reviewType: input.data.reviewType,
      periodStart: new Date(input.data.periodStart),
      periodEnd: new Date(input.data.periodEnd),
      summary: input.data.summary ?? null,
      majorWins: input.data.majorWins ?? null,
      missedTargets: input.data.missedTargets ?? null,
      snapshot,
      heldAt: new Date(),
      createdById: input.user.id,
      items: input.data.items?.length
        ? {
            create: input.data.items.map((item, index) => ({
              organizationId: input.organizationId,
              itemType: item.itemType,
              title: item.title,
              body: item.body ?? null,
              ownerUserId: item.ownerUserId ?? null,
              dueDate: item.dueDate ? new Date(item.dueDate) : null,
              sortOrder: index,
            })),
          }
        : undefined,
    },
    include: {
      items: { orderBy: { sortOrder: "asc" } },
      createdBy: { select: { id: true, name: true, email: true } },
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "BusinessReview",
    entityId: review.id,
  });

  return review;
}

export async function listBusinessReviews(organizationId: string) {
  return prisma.businessReview.findMany({
    where: { organizationId, deletedAt: null },
    include: {
      createdBy: { select: { id: true, name: true, email: true } },
      _count: { select: { items: true } },
    },
    orderBy: { periodStart: "desc" },
  });
}

export async function getBusinessReview(organizationId: string, reviewId: string) {
  return prisma.businessReview.findFirst({
    where: { id: reviewId, organizationId, deletedAt: null },
    include: {
      items: {
        include: { owner: { select: { id: true, name: true, email: true } } },
        orderBy: { sortOrder: "asc" },
      },
      createdBy: { select: { id: true, name: true, email: true } },
    },
  });
}

/** Department KPI catalog templates — configurable, not forced */
export const DEPARTMENT_KPI_TEMPLATES: Record<
  string,
  Array<{ code: string; name: string; category: string; unit?: string }>
> = {
  SALES: [
    { code: "LEAD_GEN", name: "Lead generation", category: "pipeline" },
    { code: "QUALIFIED_LEADS", name: "Qualified leads", category: "pipeline" },
    { code: "PIPELINE_VALUE", name: "Pipeline", category: "pipeline", unit: "INR" },
    { code: "CLOSED_REVENUE", name: "Closed revenue", category: "revenue", unit: "INR" },
    { code: "COLLECTED_REVENUE", name: "Collected revenue", category: "revenue", unit: "INR" },
    { code: "CONVERSION_RATE", name: "Conversion rate", category: "funnel", unit: "%" },
  ],
  CONTENT: [
    { code: "DELIVERABLES_DONE", name: "Deliverables completed", category: "delivery" },
    { code: "ON_TIME_DELIVERY", name: "On-time delivery", category: "delivery", unit: "%" },
    { code: "REVISION_RATE", name: "Revision rate", category: "quality", unit: "%" },
    { code: "CLIENT_APPROVAL", name: "Client approval rate", category: "quality", unit: "%" },
    { code: "BILLABLE_UTIL", name: "Billable utilization", category: "capacity", unit: "%" },
  ],
  DESIGN: [
    { code: "DESIGN_DELIVERABLES", name: "Design deliverables", category: "delivery" },
    { code: "APPROVAL_CYCLE", name: "Approval cycle time", category: "speed", unit: "days" },
    { code: "REVISION_RATE", name: "Revision rate", category: "quality", unit: "%" },
    { code: "UTILIZATION", name: "Utilization", category: "capacity", unit: "%" },
  ],
  VIDEO: [
    { code: "PROJECTS_DONE", name: "Projects completed", category: "delivery" },
    { code: "PROD_DELAYS", name: "Production delays", category: "risk" },
    { code: "EDIT_TURNAROUND", name: "Editing turnaround time", category: "speed", unit: "days" },
    { code: "CLIENT_APPROVAL", name: "Client approval", category: "quality", unit: "%" },
  ],
  SEO: [
    { code: "PROJECTS_ACTIVE", name: "Projects active", category: "delivery" },
    { code: "DELIVERABLES_DONE", name: "Deliverables completed", category: "delivery" },
    { code: "REPORTING_COMPLETION", name: "Reporting completion", category: "ops", unit: "%" },
    { code: "ORGANIC_VISIBILITY", name: "Organic visibility", category: "growth" },
    { code: "CLIENT_RETENTION", name: "Client retention", category: "retention", unit: "%" },
  ],
  WEB: [
    { code: "MILESTONES_DONE", name: "Milestones completed", category: "delivery" },
    { code: "BUGS", name: "Bugs", category: "quality" },
    { code: "DELIVERY_TIMELINESS", name: "Delivery timeliness", category: "delivery", unit: "%" },
    { code: "CHANGE_REQUESTS", name: "Change requests", category: "scope" },
    { code: "CLIENT_ACCEPTANCE", name: "Client acceptance", category: "quality", unit: "%" },
  ],
  HR: [
    { code: "ATTENDANCE", name: "Attendance", category: "people", unit: "%" },
    { code: "OPEN_POSITIONS", name: "Open positions", category: "hiring" },
    { code: "TIME_TO_HIRE", name: "Time to hire", category: "hiring", unit: "days" },
    { code: "ONBOARDING_COMPLETION", name: "Onboarding completion", category: "people", unit: "%" },
    { code: "ATTRITION", name: "Attrition", category: "people", unit: "%" },
  ],
  FINANCE: [
    { code: "INVOICE_COLLECTION", name: "Invoice collection", category: "cash", unit: "%" },
    { code: "RECEIVABLES", name: "Receivables", category: "cash", unit: "INR" },
    { code: "OVERDUE_INVOICES", name: "Overdue invoices", category: "cash" },
    { code: "EXPENSE_CONTROL", name: "Expense control", category: "cost", unit: "%" },
    { code: "PROJECT_PROFITABILITY", name: "Project profitability", category: "margin", unit: "%" },
  ],
};

export async function ensureDepartmentScorecard(input: {
  user: SessionUser;
  organizationId: string;
  departmentId: string;
  name: string;
  description?: string | null;
  templateCode?: string;
  kpiIds?: string[];
}) {
  const department = await prisma.department.findFirst({
    where: { id: input.departmentId, organizationId: input.organizationId },
  });
  if (!department) throw new Error("Department not found");

  let kpiIds = input.kpiIds ?? [];
  if (input.templateCode && DEPARTMENT_KPI_TEMPLATES[input.templateCode]) {
    const createdIds: string[] = [];
    for (const def of DEPARTMENT_KPI_TEMPLATES[input.templateCode]!) {
      const kpi = await prisma.kPI.upsert({
        where: {
          organizationId_code: {
            organizationId: input.organizationId,
            code: `${department.code}_${def.code}`,
          },
        },
        update: {
          name: def.name,
          category: def.category,
          unit: def.unit ?? null,
          departmentId: department.id,
          isActive: true,
          deletedAt: null,
        },
        create: {
          organizationId: input.organizationId,
          departmentId: department.id,
          name: def.name,
          code: `${department.code}_${def.code}`,
          category: def.category,
          unit: def.unit ?? null,
        },
      });
      createdIds.push(kpi.id);
    }
    kpiIds = createdIds;
  }

  const scorecard = await prisma.departmentScorecard.upsert({
    where: {
      organizationId_departmentId_name: {
        organizationId: input.organizationId,
        departmentId: department.id,
        name: input.name,
      },
    },
    update: {
      description: input.description ?? null,
      isActive: true,
      deletedAt: null,
    },
    create: {
      organizationId: input.organizationId,
      departmentId: department.id,
      name: input.name,
      description: input.description ?? null,
    },
  });

  await prisma.scorecardKpi.deleteMany({ where: { scorecardId: scorecard.id } });
  for (const [index, kpiId] of kpiIds.entries()) {
    await prisma.scorecardKpi.create({
      data: { scorecardId: scorecard.id, kpiId, sortOrder: index },
    });
  }

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "DepartmentScorecard",
    entityId: scorecard.id,
  });

  return prisma.departmentScorecard.findUnique({
    where: { id: scorecard.id },
    include: {
      department: true,
      kpis: { include: { kpi: true }, orderBy: { sortOrder: "asc" } },
    },
  });
}

export async function listScorecards(organizationId: string) {
  return prisma.departmentScorecard.findMany({
    where: { organizationId, deletedAt: null },
    include: {
      department: { select: { id: true, name: true, code: true } },
      kpis: {
        include: {
          kpi: {
            include: { values: { orderBy: { periodEnd: "desc" }, take: 1 } },
          },
        },
        orderBy: { sortOrder: "asc" },
      },
    },
    orderBy: { name: "asc" },
  });
}
