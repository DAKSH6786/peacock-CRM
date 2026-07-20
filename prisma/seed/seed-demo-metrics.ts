import type { PrismaClient } from "@prisma/client";
import {
  HealthStatus,
  MembershipRole,
  MetricType,
  OwnershipScope,
  ProgressStatus,
  XYMECategory,
} from "@prisma/client";
import bcrypt from "bcryptjs";

type DeptMap = {
  leadership: { id: string };
  sales: { id: string };
  operations: { id: string };
  creative: { id: string };
  hr: { id: string };
  finance: { id: string };
};

async function ensureUser(
  prisma: PrismaClient,
  input: {
    organizationId: string;
    departmentId: string;
    email: string;
    name: string;
    role: MembershipRole;
    employeeCode: string;
    jobTitle: string;
    isSalesRole?: boolean;
    reportingManagerId?: string;
    dateOfBirth?: Date;
    employmentStatus?: "ACTIVE" | "PROBATION";
    probationEndDate?: Date;
  },
) {
  const passwordHash = await bcrypt.hash("ChangeMeNow!123", 10);
  const office = await prisma.officeLocation.findFirst({
    where: { organizationId: input.organizationId, code: "HQ" },
  });

  const user = await prisma.user.upsert({
    where: { email: input.email },
    update: {
      name: input.name,
      passwordHash,
      status: "ACTIVE",
      organizationId: input.organizationId,
      departmentId: input.departmentId,
      jobTitle: input.jobTitle,
      deletedAt: null,
    },
    create: {
      email: input.email,
      name: input.name,
      passwordHash,
      status: "ACTIVE",
      organizationId: input.organizationId,
      departmentId: input.departmentId,
      jobTitle: input.jobTitle,
    },
  });

  await prisma.membership.upsert({
    where: {
      organizationId_userId: {
        organizationId: input.organizationId,
        userId: user.id,
      },
    },
    update: { role: input.role, deletedAt: null },
    create: {
      organizationId: input.organizationId,
      userId: user.id,
      role: input.role,
    },
  });

  const role = await prisma.role.findFirst({
    where: { organizationId: input.organizationId, code: input.role },
  });
  if (role) {
    await prisma.userRole.upsert({
      where: { userId_roleId: { userId: user.id, roleId: role.id } },
      update: { deletedAt: null, organizationId: input.organizationId },
      create: {
        organizationId: input.organizationId,
        userId: user.id,
        roleId: role.id,
      },
    });
  }

  const employee = await prisma.employee.upsert({
    where: { userId: user.id },
    update: {
      organizationId: input.organizationId,
      employeeCode: input.employeeCode,
      officialEmail: input.email,
      joiningDate: new Date("2023-04-01"),
      employmentType: "FULL_TIME",
      employmentStatus: input.employmentStatus ?? "ACTIVE",
      probationEndDate: input.probationEndDate,
      departmentId: input.departmentId,
      officeLocationId: office?.id,
      workMode: "HYBRID",
      isSalesRole: input.isSalesRole ?? false,
      reportingManagerId: input.reportingManagerId,
      dateOfBirth: input.dateOfBirth,
      deletedAt: null,
    },
    create: {
      organizationId: input.organizationId,
      userId: user.id,
      employeeCode: input.employeeCode,
      officialEmail: input.email,
      joiningDate: new Date("2023-04-01"),
      employmentType: "FULL_TIME",
      employmentStatus: input.employmentStatus ?? "ACTIVE",
      probationEndDate: input.probationEndDate,
      departmentId: input.departmentId,
      officeLocationId: office?.id,
      workMode: "HYBRID",
      isSalesRole: input.isSalesRole ?? false,
      reportingManagerId: input.reportingManagerId,
      dateOfBirth: input.dateOfBirth,
    },
  });

  return { user, employee };
}

export async function seedDemoMetrics(
  prisma: PrismaClient,
  input: {
    organizationId: string;
    adminUserId: string;
    departments: DeptMap;
  },
) {
  const { organizationId, adminUserId, departments } = input;
  const now = new Date();
  const monthStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
  const today = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );

  const manager = await ensureUser(prisma, {
    organizationId,
    departmentId: departments.operations.id,
    email: "manager@digitalpeacock.local",
    name: "Ops Manager",
    role: MembershipRole.MANAGER,
    employeeCode: "DP0002",
    jobTitle: "Delivery Manager",
  });

  const salesperson = await ensureUser(prisma, {
    organizationId,
    departmentId: departments.sales.id,
    email: "sales@digitalpeacock.local",
    name: "Sales Lead",
    role: MembershipRole.SALES,
    employeeCode: "DP0003",
    jobTitle: "Sales Lead",
    isSalesRole: true,
    reportingManagerId: manager.employee.id,
  });

  const financeUser = await ensureUser(prisma, {
    organizationId,
    departmentId: departments.finance.id,
    email: "finance@digitalpeacock.local",
    name: "Finance Controller",
    role: MembershipRole.FINANCE,
    employeeCode: "DP0004",
    jobTitle: "Finance Controller",
    reportingManagerId: manager.employee.id,
  });

  const hrUser = await ensureUser(prisma, {
    organizationId,
    departmentId: departments.hr.id,
    email: "hr@digitalpeacock.local",
    name: "HR Partner",
    role: MembershipRole.HR,
    employeeCode: "DP0005",
    jobTitle: "HR Partner",
    reportingManagerId: manager.employee.id,
    dateOfBirth: new Date(
      Date.UTC(1992, now.getUTCMonth(), Math.min(now.getUTCDate() + 5, 28)),
    ),
  });

  const employeeUser = await ensureUser(prisma, {
    organizationId,
    departmentId: departments.creative.id,
    email: "employee@digitalpeacock.local",
    name: "Creative Associate",
    role: MembershipRole.EMPLOYEE,
    employeeCode: "DP0006",
    jobTitle: "Designer",
    reportingManagerId: manager.employee.id,
    employmentStatus: "PROBATION",
    probationEndDate: new Date(today.getTime() + 14 * 86400000),
    dateOfBirth: new Date(
      Date.UTC(1995, now.getUTCMonth(), Math.min(now.getUTCDate() + 10, 28)),
    ),
  });

  const adminEmployee = await prisma.employee.findUniqueOrThrow({
    where: { userId: adminUserId },
  });

  // CRM foundation
  const source = await prisma.leadSource.upsert({
    where: { organizationId_code: { organizationId, code: "WEB" } },
    update: { name: "Website", deletedAt: null },
    create: { organizationId, name: "Website", code: "WEB" },
  });

  const openStatus = await prisma.leadStatus.upsert({
    where: { organizationId_code: { organizationId, code: "OPEN" } },
    update: { name: "Open", deletedAt: null },
    create: {
      organizationId,
      name: "Open",
      code: "OPEN",
      sortOrder: 1,
    },
  });

  const statusDefs = [
    { name: "New lead", code: "NEW", sortOrder: 1 },
    { name: "Qualification", code: "QUALIFICATION", sortOrder: 2 },
    { name: "Contacted", code: "CONTACTED", sortOrder: 3 },
    { name: "Discovery", code: "DISCOVERY", sortOrder: 4 },
    { name: "Proposal required", code: "PROPOSAL_REQUIRED", sortOrder: 5 },
    { name: "Proposal sent", code: "PROPOSAL_SENT", sortOrder: 6 },
    { name: "Negotiation", code: "NEGOTIATION", sortOrder: 7 },
    { name: "Won", code: "WON", sortOrder: 8, isWon: true },
    { name: "Lost", code: "LOST", sortOrder: 9, isLost: true },
    { name: "Nurturing", code: "NURTURING", sortOrder: 10 },
    { name: "Disqualified", code: "DISQUALIFIED", sortOrder: 11, isLost: true },
  ] as const;

  for (const def of statusDefs) {
    await prisma.leadStatus.upsert({
      where: { organizationId_code: { organizationId, code: def.code } },
      update: {
        name: def.name,
        sortOrder: def.sortOrder,
        isWon: "isWon" in def ? Boolean(def.isWon) : false,
        isLost: "isLost" in def ? Boolean(def.isLost) : false,
        deletedAt: null,
      },
      create: {
        organizationId,
        name: def.name,
        code: def.code,
        sortOrder: def.sortOrder,
        isWon: "isWon" in def ? Boolean(def.isWon) : false,
        isLost: "isLost" in def ? Boolean(def.isLost) : false,
      },
    });
  }

  const lostReason = await prisma.lostReason.upsert({
    where: { organizationId_code: { organizationId, code: "BUDGET" } },
    update: { name: "Budget", deletedAt: null },
    create: { organizationId, name: "Budget", code: "BUDGET" },
  });

  const pipeline = await prisma.pipeline.upsert({
    where: { organizationId_code: { organizationId, code: "DEFAULT" } },
    update: { name: "Default pipeline", isDefault: true, deletedAt: null },
    create: {
      organizationId,
      name: "Default pipeline",
      code: "DEFAULT",
      isDefault: true,
    },
  });

  const stageDefs = [
    {
      name: "New",
      code: "NEW",
      sortOrder: 1,
      probability: 5,
      color: "#64748B",
      staleAfterDays: 7,
    },
    {
      name: "Qualification",
      code: "QUAL",
      sortOrder: 2,
      probability: 15,
      color: "#0EA5E9",
      requiredFields: ["email", "companyName"],
      staleAfterDays: 10,
    },
    {
      name: "Contacted",
      code: "CONT",
      sortOrder: 3,
      probability: 20,
      color: "#06B6D4",
      staleAfterDays: 7,
    },
    {
      name: "Discovery",
      code: "DISC",
      sortOrder: 4,
      probability: 30,
      color: "#14B8A6",
      requiredFields: ["estimatedValueMinor"],
      staleAfterDays: 14,
    },
    {
      name: "Proposal required",
      code: "PROP_REQ",
      sortOrder: 5,
      probability: 40,
      color: "#F59E0B",
      staleAfterDays: 7,
    },
    {
      name: "Proposal sent",
      code: "PROP",
      sortOrder: 6,
      probability: 55,
      color: "#F97316",
      staleAfterDays: 10,
    },
    {
      name: "Negotiation",
      code: "NEGO",
      sortOrder: 7,
      probability: 70,
      color: "#8B5CF6",
      staleAfterDays: 14,
    },
    {
      name: "Won",
      code: "WON",
      sortOrder: 8,
      probability: 100,
      color: "#16A34A",
      isClosedWon: true,
    },
    {
      name: "Lost",
      code: "LOST",
      sortOrder: 9,
      probability: 0,
      color: "#DC2626",
      isClosedLost: true,
    },
    {
      name: "Nurturing",
      code: "NURT",
      sortOrder: 10,
      probability: 10,
      color: "#A855F7",
      staleAfterDays: 30,
    },
  ] as const;

  const stages: Record<string, string> = {};
  for (const def of stageDefs) {
    const stage = await prisma.pipelineStage.upsert({
      where: {
        pipelineId_code: { pipelineId: pipeline.id, code: def.code },
      },
      update: {
        name: def.name,
        sortOrder: def.sortOrder,
        probability: def.probability,
        color: "color" in def ? def.color : null,
        requiredFields:
          "requiredFields" in def ? [...(def.requiredFields as unknown as string[])] : [],
        staleAfterDays:
          "staleAfterDays" in def ? (def.staleAfterDays as number) : null,
        isClosedWon: "isClosedWon" in def ? def.isClosedWon : false,
        isClosedLost: "isClosedLost" in def ? def.isClosedLost : false,
        deletedAt: null,
        organizationId,
      },
      create: {
        organizationId,
        pipelineId: pipeline.id,
        name: def.name,
        code: def.code,
        sortOrder: def.sortOrder,
        probability: def.probability,
        color: "color" in def ? def.color : null,
        requiredFields:
          "requiredFields" in def ? [...(def.requiredFields as unknown as string[])] : [],
        staleAfterDays:
          "staleAfterDays" in def ? (def.staleAfterDays as number) : null,
        isClosedWon: "isClosedWon" in def ? Boolean(def.isClosedWon) : false,
        isClosedLost: "isClosedLost" in def ? Boolean(def.isClosedLost) : false,
      },
    });
    stages[def.code] = stage.id;
  }

  const company = await prisma.clientCompany.upsert({
    where: { id: "seed-company-northstar" },
    update: {
      organizationId,
      name: "Northstar Retail",
      domain: "northstar.example",
      deletedAt: null,
    },
    create: {
      id: "seed-company-northstar",
      organizationId,
      name: "Northstar Retail",
      domain: "northstar.example",
      normalizedName: "northstar retail",
      normalizedDomain: "northstar.example",
    },
  });

  await prisma.contact.upsert({
    where: { id: "seed-contact-priya" },
    update: {
      organizationId,
      companyId: company.id,
      firstName: "Priya",
      lastName: "Shah",
      email: "priya@northstar.example",
      deletedAt: null,
    },
    create: {
      id: "seed-contact-priya",
      organizationId,
      companyId: company.id,
      firstName: "Priya",
      lastName: "Shah",
      email: "priya@northstar.example",
    },
  });

  const lead = await prisma.lead.upsert({
    where: { id: "seed-lead-anika" },
    update: {
      organizationId,
      personName: "Anika Mehta",
      companyName: "Northstar Retail",
      email: "anika@northstar.example",
      sourceId: source.id,
      statusId: openStatus.id,
      pipelineId: pipeline.id,
      stageId: stages.PROP,
      companyId: company.id,
      assignedUserId: salesperson.user.id,
      estimatedValueMinor: 45000000,
      deletedAt: null,
    },
    create: {
      id: "seed-lead-anika",
      organizationId,
      personName: "Anika Mehta",
      companyName: "Northstar Retail",
      email: "anika@northstar.example",
      sourceId: source.id,
      statusId: openStatus.id,
      pipelineId: pipeline.id,
      stageId: stages.PROP,
      companyId: company.id,
      assignedUserId: salesperson.user.id,
      estimatedValueMinor: 45000000,
      createdById: salesperson.user.id,
    },
  });

  await prisma.lead.upsert({
    where: { id: "seed-lead-ravi" },
    update: {
      organizationId,
      personName: "Ravi Kapoor",
      companyName: "Orbit Logistics",
      email: "ravi@orbit.example",
      sourceId: source.id,
      statusId: openStatus.id,
      assignedUserId: salesperson.user.id,
      createdAt: new Date(monthStart.getTime() + 2 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-lead-ravi",
      organizationId,
      personName: "Ravi Kapoor",
      companyName: "Orbit Logistics",
      email: "ravi@orbit.example",
      sourceId: source.id,
      statusId: openStatus.id,
      assignedUserId: salesperson.user.id,
      createdAt: new Date(monthStart.getTime() + 2 * 86400000),
      createdById: salesperson.user.id,
    },
  });

  await prisma.followUp.upsert({
    where: { id: "seed-followup-1" },
    update: {
      organizationId,
      leadId: lead.id,
      dueAt: new Date(today.getTime() + 86400000),
      assignedUserId: salesperson.user.id,
      notes: "Send revised proposal",
      completedAt: null,
      deletedAt: null,
    },
    create: {
      id: "seed-followup-1",
      organizationId,
      leadId: lead.id,
      dueAt: new Date(today.getTime() + 86400000),
      assignedUserId: salesperson.user.id,
      notes: "Send revised proposal",
    },
  });

  await prisma.followUp.upsert({
    where: { id: "seed-followup-overdue" },
    update: {
      organizationId,
      leadId: lead.id,
      dueAt: new Date(today.getTime() - 3 * 86400000),
      assignedUserId: salesperson.user.id,
      notes: "Overdue discovery call",
      completedAt: null,
      deletedAt: null,
    },
    create: {
      id: "seed-followup-overdue",
      organizationId,
      leadId: lead.id,
      dueAt: new Date(today.getTime() - 3 * 86400000),
      assignedUserId: salesperson.user.id,
      notes: "Overdue discovery call",
    },
  });

  const openDeal = await prisma.deal.upsert({
    where: { id: "seed-deal-open" },
    update: {
      organizationId,
      name: "Northstar brand refresh",
      companyId: company.id,
      leadId: lead.id,
      pipelineId: pipeline.id,
      stageId: stages.NEGO,
      ownerUserId: salesperson.user.id,
      valueMinor: 32000000,
      probability: 70,
      closedAt: null,
      deletedAt: null,
    },
    create: {
      id: "seed-deal-open",
      organizationId,
      name: "Northstar brand refresh",
      companyId: company.id,
      leadId: lead.id,
      pipelineId: pipeline.id,
      stageId: stages.NEGO,
      ownerUserId: salesperson.user.id,
      valueMinor: 32000000,
      probability: 70,
    },
  });

  await prisma.deal.upsert({
    where: { id: "seed-deal-won" },
    update: {
      organizationId,
      name: "Orbit website rebuild",
      pipelineId: pipeline.id,
      stageId: stages.WON,
      ownerUserId: salesperson.user.id,
      valueMinor: 18000000,
      probability: 100,
      closedAt: new Date(monthStart.getTime() + 5 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-deal-won",
      organizationId,
      name: "Orbit website rebuild",
      pipelineId: pipeline.id,
      stageId: stages.WON,
      ownerUserId: salesperson.user.id,
      valueMinor: 18000000,
      probability: 100,
      closedAt: new Date(monthStart.getTime() + 5 * 86400000),
    },
  });

  await prisma.deal.upsert({
    where: { id: "seed-deal-lost" },
    update: {
      organizationId,
      name: "Atlas campaign pitch",
      pipelineId: pipeline.id,
      stageId: stages.LOST,
      ownerUserId: salesperson.user.id,
      valueMinor: 9000000,
      probability: 0,
      lostReasonId: lostReason.id,
      closedAt: new Date(monthStart.getTime() + 8 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-deal-lost",
      organizationId,
      name: "Atlas campaign pitch",
      pipelineId: pipeline.id,
      stageId: stages.LOST,
      ownerUserId: salesperson.user.id,
      valueMinor: 9000000,
      probability: 0,
      lostReasonId: lostReason.id,
      closedAt: new Date(monthStart.getTime() + 8 * 86400000),
    },
  });

  await prisma.deal.upsert({
    where: { id: "seed-deal-discovery" },
    update: {
      organizationId,
      name: "Helix product launch",
      pipelineId: pipeline.id,
      stageId: stages.DISC,
      ownerUserId: salesperson.user.id,
      valueMinor: 15000000,
      probability: 20,
      closedAt: null,
      deletedAt: null,
    },
    create: {
      id: "seed-deal-discovery",
      organizationId,
      name: "Helix product launch",
      pipelineId: pipeline.id,
      stageId: stages.DISC,
      ownerUserId: salesperson.user.id,
      valueMinor: 15000000,
      probability: 20,
    },
  });

  const quote = await prisma.quote.upsert({
    where: { id: "seed-quote-1" },
    update: {
      organizationId,
      quoteNumber: "DP-QT-1001",
      companyId: company.id,
      dealId: openDeal.id,
      status: "SENT",
      totalMinor: 32000000,
      issueDate: monthStart,
      deletedAt: null,
    },
    create: {
      id: "seed-quote-1",
      organizationId,
      quoteNumber: "DP-QT-1001",
      companyId: company.id,
      dealId: openDeal.id,
      status: "SENT",
      totalMinor: 32000000,
      issueDate: monthStart,
      createdById: salesperson.user.id,
    },
  });

  const project = await prisma.project.upsert({
    where: { id: "seed-project-northstar" },
    update: {
      organizationId,
      companyId: company.id,
      dealId: openDeal.id,
      name: "Northstar brand system",
      code: "NS-BRAND",
      status: "ACTIVE",
      startDate: monthStart,
      endDate: new Date(monthStart.getTime() + 60 * 86400000),
      budgetMinor: 28000000,
      deletedAt: null,
    },
    create: {
      id: "seed-project-northstar",
      organizationId,
      companyId: company.id,
      dealId: openDeal.id,
      name: "Northstar brand system",
      code: "NS-BRAND",
      status: "ACTIVE",
      startDate: monthStart,
      endDate: new Date(monthStart.getTime() + 60 * 86400000),
      budgetMinor: 28000000,
      createdById: manager.user.id,
    },
  });

  await prisma.project.upsert({
    where: { id: "seed-project-risk" },
    update: {
      organizationId,
      name: "Atlas migration",
      code: "AT-MIG",
      status: "AT_RISK",
      deletedAt: null,
    },
    create: {
      id: "seed-project-risk",
      organizationId,
      name: "Atlas migration",
      code: "AT-MIG",
      status: "AT_RISK",
      createdById: manager.user.id,
    },
  });

  await prisma.projectService.deleteMany({
    where: { projectId: project.id },
  });
  await prisma.projectService.createMany({
    data: [
      {
        organizationId,
        projectId: project.id,
        name: "Brand strategy",
      },
      {
        organizationId,
        projectId: project.id,
        name: "Visual identity",
      },
    ],
  });

  await prisma.projectMember.upsert({
    where: {
      projectId_employeeId: {
        projectId: project.id,
        employeeId: employeeUser.employee.id,
      },
    },
    update: { organizationId, role: "Designer", allocationPct: 80 },
    create: {
      organizationId,
      projectId: project.id,
      employeeId: employeeUser.employee.id,
      role: "Designer",
      allocationPct: 80,
    },
  });

  await prisma.projectMember.upsert({
    where: {
      projectId_employeeId: {
        projectId: project.id,
        employeeId: manager.employee.id,
      },
    },
    update: { organizationId, role: "PM", allocationPct: 40 },
    create: {
      organizationId,
      projectId: project.id,
      employeeId: manager.employee.id,
      role: "PM",
      allocationPct: 40,
    },
  });

  await prisma.resourceAllocation.deleteMany({
    where: {
      organizationId,
      projectId: project.id,
      employeeId: {
        in: [employeeUser.employee.id, manager.employee.id],
      },
    },
  });
  await prisma.resourceAllocation.createMany({
    data: [
      {
        organizationId,
        projectId: project.id,
        employeeId: employeeUser.employee.id,
        startDate: monthStart,
        allocationPct: 80,
      },
      {
        organizationId,
        projectId: project.id,
        employeeId: manager.employee.id,
        startDate: monthStart,
        allocationPct: 40,
      },
    ],
  });

  await prisma.projectMilestone.upsert({
    where: { id: "seed-milestone-1" },
    update: {
      organizationId,
      projectId: project.id,
      title: "Moodboard approval",
      dueDate: new Date(today.getTime() + 5 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-milestone-1",
      organizationId,
      projectId: project.id,
      title: "Moodboard approval",
      dueDate: new Date(today.getTime() + 5 * 86400000),
    },
  });

  const task = await prisma.task.upsert({
    where: { id: "seed-task-1" },
    update: {
      organizationId,
      projectId: project.id,
      title: "Finalize logo options",
      status: "IN_PROGRESS",
      assigneeId: employeeUser.user.id,
      dueDate: new Date(today.getTime() + 2 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-task-1",
      organizationId,
      projectId: project.id,
      title: "Finalize logo options",
      status: "IN_PROGRESS",
      assigneeId: employeeUser.user.id,
      dueDate: new Date(today.getTime() + 2 * 86400000),
      createdById: manager.user.id,
    },
  });

  await prisma.task.upsert({
    where: { id: "seed-task-overdue" },
    update: {
      organizationId,
      projectId: project.id,
      title: "Collect brand assets",
      status: "TODO",
      assigneeId: employeeUser.user.id,
      dueDate: new Date(today.getTime() - 2 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-task-overdue",
      organizationId,
      projectId: project.id,
      title: "Collect brand assets",
      status: "TODO",
      assigneeId: employeeUser.user.id,
      dueDate: new Date(today.getTime() - 2 * 86400000),
      createdById: manager.user.id,
    },
  });

  const deliverable = await prisma.deliverable.upsert({
    where: { id: "seed-deliverable-1" },
    update: {
      organizationId,
      projectId: project.id,
      title: "Primary logo set",
      status: "IN_REVIEW",
      dueDate: new Date(today.getTime() + 3 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-deliverable-1",
      organizationId,
      projectId: project.id,
      title: "Primary logo set",
      status: "IN_REVIEW",
      dueDate: new Date(today.getTime() + 3 * 86400000),
    },
  });

  await prisma.deliverableApproval.deleteMany({
    where: { deliverableId: deliverable.id },
  });
  await prisma.deliverableApproval.create({
    data: {
      organizationId,
      deliverableId: deliverable.id,
      status: "PENDING",
      reviewerId: manager.user.id,
    },
  });

  await prisma.timeEntry.deleteMany({
    where: {
      organizationId,
      employeeId: employeeUser.employee.id,
      date: { gte: monthStart },
    },
  });
  await prisma.timeEntry.createMany({
    data: [
      {
        organizationId,
        projectId: project.id,
        taskId: task.id,
        employeeId: employeeUser.employee.id,
        date: today,
        hours: 6,
        billable: true,
      },
      {
        organizationId,
        projectId: project.id,
        employeeId: employeeUser.employee.id,
        date: new Date(today.getTime() - 86400000),
        hours: 2,
        billable: false,
      },
    ],
  });

  await prisma.projectProfitabilitySnapshot.upsert({
    where: {
      projectId_asOfDate: { projectId: project.id, asOfDate: today },
    },
    update: {
      organizationId,
      revenueMinor: 18000000,
      costMinor: 7200000,
      profitMinor: 10800000,
    },
    create: {
      organizationId,
      projectId: project.id,
      asOfDate: today,
      revenueMinor: 18000000,
      costMinor: 7200000,
      profitMinor: 10800000,
    },
  });

  // Finance
  const invoicePaid = await prisma.invoice.upsert({
    where: { id: "seed-invoice-paid" },
    update: {
      organizationId,
      invoiceNumber: "DP-INV-2001",
      companyId: company.id,
      projectId: project.id,
      dealId: openDeal.id,
      quoteId: quote.id,
      issueDate: monthStart,
      dueDate: new Date(monthStart.getTime() + 15 * 86400000),
      totalMinor: 12000000,
      amountPaidMinor: 12000000,
      balanceMinor: 0,
      status: "PAID",
      deletedAt: null,
    },
    create: {
      id: "seed-invoice-paid",
      organizationId,
      invoiceNumber: "DP-INV-2001",
      companyId: company.id,
      projectId: project.id,
      dealId: openDeal.id,
      quoteId: quote.id,
      issueDate: monthStart,
      dueDate: new Date(monthStart.getTime() + 15 * 86400000),
      totalMinor: 12000000,
      amountPaidMinor: 12000000,
      balanceMinor: 0,
      status: "PAID",
      createdById: financeUser.user.id,
    },
  });

  await prisma.invoice.upsert({
    where: { id: "seed-invoice-open" },
    update: {
      organizationId,
      invoiceNumber: "DP-INV-2002",
      companyId: company.id,
      projectId: project.id,
      issueDate: new Date(monthStart.getTime() + 3 * 86400000),
      dueDate: new Date(today.getTime() + 10 * 86400000),
      totalMinor: 8000000,
      amountPaidMinor: 2000000,
      balanceMinor: 6000000,
      status: "PARTIAL",
      deletedAt: null,
    },
    create: {
      id: "seed-invoice-open",
      organizationId,
      invoiceNumber: "DP-INV-2002",
      companyId: company.id,
      projectId: project.id,
      issueDate: new Date(monthStart.getTime() + 3 * 86400000),
      dueDate: new Date(today.getTime() + 10 * 86400000),
      totalMinor: 8000000,
      amountPaidMinor: 2000000,
      balanceMinor: 6000000,
      status: "PARTIAL",
      createdById: financeUser.user.id,
    },
  });

  await prisma.invoice.upsert({
    where: { id: "seed-invoice-overdue" },
    update: {
      organizationId,
      invoiceNumber: "DP-INV-1990",
      companyId: company.id,
      issueDate: new Date(monthStart.getTime() - 40 * 86400000),
      dueDate: new Date(today.getTime() - 20 * 86400000),
      totalMinor: 4500000,
      amountPaidMinor: 0,
      balanceMinor: 4500000,
      status: "OVERDUE",
      deletedAt: null,
    },
    create: {
      id: "seed-invoice-overdue",
      organizationId,
      invoiceNumber: "DP-INV-1990",
      companyId: company.id,
      issueDate: new Date(monthStart.getTime() - 40 * 86400000),
      dueDate: new Date(today.getTime() - 20 * 86400000),
      totalMinor: 4500000,
      amountPaidMinor: 0,
      balanceMinor: 4500000,
      status: "OVERDUE",
      createdById: financeUser.user.id,
    },
  });

  await prisma.payment.upsert({
    where: { id: "seed-payment-1" },
    update: {
      organizationId,
      paymentNumber: "PAY-9001",
      amountMinor: 12000000,
      receivedAt: new Date(monthStart.getTime() + 6 * 86400000),
      method: "NEFT",
      deletedAt: null,
    },
    create: {
      id: "seed-payment-1",
      organizationId,
      paymentNumber: "PAY-9001",
      amountMinor: 12000000,
      receivedAt: new Date(monthStart.getTime() + 6 * 86400000),
      method: "NEFT",
      createdById: financeUser.user.id,
    },
  });

  await prisma.payment.upsert({
    where: { id: "seed-payment-2" },
    update: {
      organizationId,
      paymentNumber: "PAY-9002",
      amountMinor: 2000000,
      receivedAt: new Date(monthStart.getTime() + 10 * 86400000),
      method: "UPI",
      deletedAt: null,
    },
    create: {
      id: "seed-payment-2",
      organizationId,
      paymentNumber: "PAY-9002",
      amountMinor: 2000000,
      receivedAt: new Date(monthStart.getTime() + 10 * 86400000),
      method: "UPI",
      createdById: financeUser.user.id,
    },
  });

  const vendor = await prisma.vendor.upsert({
    where: { id: "seed-vendor-1" },
    update: {
      organizationId,
      name: "Pixel Press",
      code: "VND-PP",
      deletedAt: null,
    },
    create: {
      id: "seed-vendor-1",
      organizationId,
      name: "Pixel Press",
      code: "VND-PP",
    },
  });

  await prisma.expense.upsert({
    where: { id: "seed-expense-1" },
    update: {
      organizationId,
      vendorId: vendor.id,
      title: "Print samples",
      amountMinor: 450000,
      spentAt: new Date(monthStart.getTime() + 4 * 86400000),
      status: "APPROVED",
      deletedAt: null,
    },
    create: {
      id: "seed-expense-1",
      organizationId,
      vendorId: vendor.id,
      title: "Print samples",
      amountMinor: 450000,
      spentAt: new Date(monthStart.getTime() + 4 * 86400000),
      status: "APPROVED",
      createdById: employeeUser.user.id,
    },
  });

  await prisma.vendorBill.upsert({
    where: { id: "seed-vendor-bill-1" },
    update: {
      organizationId,
      vendorId: vendor.id,
      billNumber: "VB-441",
      amountMinor: 275000,
      status: "OPEN",
      deletedAt: null,
    },
    create: {
      id: "seed-vendor-bill-1",
      organizationId,
      vendorId: vendor.id,
      billNumber: "VB-441",
      amountMinor: 275000,
      status: "OPEN",
    },
  });

  // People / HR / attendance
  for (const employee of [
    adminEmployee,
    manager.employee,
    salesperson.employee,
    financeUser.employee,
    hrUser.employee,
    employeeUser.employee,
  ]) {
    await prisma.attendanceRecord.upsert({
      where: {
        employeeId_date: { employeeId: employee.id, date: today },
      },
      update: {
        organizationId,
        status: "PRESENT",
        workMode: "HYBRID",
      },
      create: {
        organizationId,
        employeeId: employee.id,
        date: today,
        status: "PRESENT",
        workMode: "HYBRID",
      },
    });

    await prisma.employeeMonthlyCost.upsert({
      where: {
        employeeId_month: { employeeId: employee.id, month: monthStart },
      },
      update: {
        organizationId,
        costMinor: 25000000,
      },
      create: {
        organizationId,
        employeeId: employee.id,
        month: monthStart,
        costMinor: 25000000,
      },
    });
  }

  const leaveType = await prisma.leaveType.upsert({
    where: { organizationId_code: { organizationId, code: "AL" } },
    update: { name: "Annual Leave", deletedAt: null },
    create: {
      organizationId,
      name: "Annual Leave",
      code: "AL",
      paid: true,
      maxDaysPerYear: 18,
    },
  });

  await prisma.leaveBalance.upsert({
    where: {
      employeeId_leaveTypeId_year: {
        employeeId: employeeUser.employee.id,
        leaveTypeId: leaveType.id,
        year: now.getUTCFullYear(),
      },
    },
    update: { organizationId, balanceDays: 12 },
    create: {
      organizationId,
      employeeId: employeeUser.employee.id,
      leaveTypeId: leaveType.id,
      year: now.getUTCFullYear(),
      balanceDays: 12,
    },
  });

  await prisma.leaveRequest.upsert({
    where: { id: "seed-leave-pending" },
    update: {
      organizationId,
      employeeId: employeeUser.employee.id,
      leaveTypeId: leaveType.id,
      startDate: new Date(today.getTime() + 7 * 86400000),
      endDate: new Date(today.getTime() + 8 * 86400000),
      days: 2,
      status: "PENDING",
      reason: "Family travel",
      deletedAt: null,
    },
    create: {
      id: "seed-leave-pending",
      organizationId,
      employeeId: employeeUser.employee.id,
      leaveTypeId: leaveType.id,
      startDate: new Date(today.getTime() + 7 * 86400000),
      endDate: new Date(today.getTime() + 8 * 86400000),
      days: 2,
      status: "PENDING",
      reason: "Family travel",
    },
  });

  await prisma.leaveRequest.upsert({
    where: { id: "seed-leave-active" },
    update: {
      organizationId,
      employeeId: hrUser.employee.id,
      leaveTypeId: leaveType.id,
      startDate: today,
      endDate: today,
      days: 1,
      status: "APPROVED",
      deletedAt: null,
    },
    create: {
      id: "seed-leave-active",
      organizationId,
      employeeId: hrUser.employee.id,
      leaveTypeId: leaveType.id,
      startDate: today,
      endDate: today,
      days: 1,
      status: "APPROVED",
    },
  });

  await prisma.attendanceCorrectionRequest.upsert({
    where: { id: "seed-attendance-correction" },
    update: {
      organizationId,
      employeeId: employeeUser.employee.id,
      date: new Date(today.getTime() - 86400000),
      reason: "Missed checkout",
      status: "PENDING",
    },
    create: {
      id: "seed-attendance-correction",
      organizationId,
      employeeId: employeeUser.employee.id,
      date: new Date(today.getTime() - 86400000),
      reason: "Missed checkout",
      status: "PENDING",
    },
  });

  await prisma.announcement.upsert({
    where: { id: "seed-announcement-1" },
    update: {
      organizationId,
      title: "Q2 planning kickoff tomorrow",
      body: "Bring your department priorities to the all-hands.",
      publishedAt: today,
      deletedAt: null,
    },
    create: {
      id: "seed-announcement-1",
      organizationId,
      title: "Q2 planning kickoff tomorrow",
      body: "Bring your department priorities to the all-hands.",
      publishedAt: today,
      createdById: hrUser.user.id,
    },
  });

  await prisma.employeeDocument.upsert({
    where: { id: "seed-doc-1" },
    update: {
      organizationId,
      employeeId: employeeUser.employee.id,
      title: "Offer letter",
      expiresAt: new Date(today.getTime() + 20 * 86400000),
      deletedAt: null,
    },
    create: {
      id: "seed-doc-1",
      organizationId,
      employeeId: employeeUser.employee.id,
      title: "Offer letter",
      expiresAt: new Date(today.getTime() + 20 * 86400000),
    },
  });

  const job = await prisma.recruitmentJob.upsert({
    where: {
      organizationId_code: { organizationId, code: "DES-02" },
    },
    update: {
      title: "Senior Designer",
      departmentId: departments.creative.id,
      status: "OPEN",
      deletedAt: null,
    },
    create: {
      organizationId,
      title: "Senior Designer",
      code: "DES-02",
      departmentId: departments.creative.id,
      status: "OPEN",
      openings: 1,
    },
  });

  const candidate = await prisma.candidate.upsert({
    where: {
      organizationId_email: {
        organizationId,
        email: "candidate@example.com",
      },
    },
    update: {
      firstName: "Neha",
      lastName: "Iyer",
      deletedAt: null,
    },
    create: {
      organizationId,
      firstName: "Neha",
      lastName: "Iyer",
      email: "candidate@example.com",
    },
  });

  await prisma.candidateApplication.upsert({
    where: {
      jobId_candidateId: { jobId: job.id, candidateId: candidate.id },
    },
    update: { organizationId, status: "INTERVIEW" },
    create: {
      organizationId,
      jobId: job.id,
      candidateId: candidate.id,
      status: "INTERVIEW",
    },
  });

  const onboarding = await prisma.onboardingChecklist.upsert({
    where: { id: "seed-onboarding-1" },
    update: {
      organizationId,
      employeeId: employeeUser.employee.id,
      title: "Creative associate onboarding",
      status: "IN_PROGRESS",
    },
    create: {
      id: "seed-onboarding-1",
      organizationId,
      employeeId: employeeUser.employee.id,
      title: "Creative associate onboarding",
      status: "IN_PROGRESS",
    },
  });

  await prisma.onboardingTask.deleteMany({
    where: { checklistId: onboarding.id },
  });
  await prisma.onboardingTask.create({
    data: {
      checklistId: onboarding.id,
      title: "Complete IT access form",
      dueDate: new Date(today.getTime() + 3 * 86400000),
      assigneeId: hrUser.user.id,
    },
  });

  const asset = await prisma.companyAsset.upsert({
    where: { id: "seed-asset-1" },
    update: {
      organizationId,
      name: "MacBook Pro 14",
      assetTag: "DP-LAP-014",
      status: "ASSIGNED",
      deletedAt: null,
    },
    create: {
      id: "seed-asset-1",
      organizationId,
      name: "MacBook Pro 14",
      assetTag: "DP-LAP-014",
      status: "ASSIGNED",
    },
  });

  await prisma.assetAssignment.deleteMany({
    where: { assetId: asset.id, returnedAt: null },
  });
  await prisma.assetAssignment.create({
    data: {
      organizationId,
      assetId: asset.id,
      employeeId: employeeUser.employee.id,
      assignedAt: monthStart,
    },
  });

  // Objectives / risks / approvals / XYME / sales
  await prisma.objective.upsert({
    where: { id: "seed-obj-company" },
    update: {
      organizationId,
      title: "Grow retainer revenue",
      description: "Increase recurring revenue across retainers this FY.",
      scope: OwnershipScope.COMPANY,
      progressPct: 62,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      priority: "HIGH",
      primaryOwnerId: adminUserId,
      tags: ["revenue", "retainers"],
      deletedAt: null,
    },
    create: {
      id: "seed-obj-company",
      organizationId,
      title: "Grow retainer revenue",
      description: "Increase recurring revenue across retainers this FY.",
      scope: OwnershipScope.COMPANY,
      progressPct: 62,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      priority: "HIGH",
      primaryOwnerId: adminUserId,
      tags: ["revenue", "retainers"],
      createdById: adminUserId,
    },
  });

  await prisma.objective.upsert({
    where: { id: "seed-obj-sales" },
    update: {
      organizationId,
      title: "Improve win rate",
      description: "Lift qualified-to-won conversion for enterprise deals.",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.sales.id,
      parentId: "seed-obj-company",
      progressPct: 48,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      primaryOwnerId: salesperson.user.id,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-sales",
      organizationId,
      title: "Improve win rate",
      description: "Lift qualified-to-won conversion for enterprise deals.",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.sales.id,
      parentId: "seed-obj-company",
      progressPct: 48,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      primaryOwnerId: salesperson.user.id,
      createdById: salesperson.user.id,
    },
  });

  await prisma.objective.upsert({
    where: { id: "seed-obj-ops" },
    update: {
      organizationId,
      title: "On-time delivery",
      description: "Keep delivery SLAs green across active projects.",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.operations.id,
      parentId: "seed-obj-company",
      progressPct: 71,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.GREEN,
      quarter: "Q2",
      primaryOwnerId: manager.user.id,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-ops",
      organizationId,
      title: "On-time delivery",
      description: "Keep delivery SLAs green across active projects.",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.operations.id,
      parentId: "seed-obj-company",
      progressPct: 71,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.GREEN,
      quarter: "Q2",
      primaryOwnerId: manager.user.id,
      createdById: manager.user.id,
    },
  });

  await prisma.objective.upsert({
    where: { id: "seed-obj-individual" },
    update: {
      organizationId,
      title: "Close two enterprise retainers",
      scope: OwnershipScope.INDIVIDUAL,
      parentId: "seed-obj-sales",
      departmentId: departments.sales.id,
      progressPct: 50,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      primaryOwnerId: salesperson.user.id,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-individual",
      organizationId,
      title: "Close two enterprise retainers",
      scope: OwnershipScope.INDIVIDUAL,
      parentId: "seed-obj-sales",
      departmentId: departments.sales.id,
      progressPct: 50,
      status: ProgressStatus.IN_PROGRESS,
      health: HealthStatus.AMBER,
      quarter: "Q2",
      primaryOwnerId: salesperson.user.id,
      createdById: salesperson.user.id,
    },
  });

  await prisma.keyResult.upsert({
    where: { id: "seed-kr-revenue" },
    update: {
      organizationId,
      objectiveId: "seed-obj-company",
      title: "Retainer ARR",
      metricType: MetricType.CURRENCY,
      baseline: 8000000,
      target: 12000000,
      currentValue: 9800000,
      unit: "INR",
      progressPct: 45,
      ownerUserId: adminUserId,
      updateFrequency: "MONTHLY",
      confidenceScore: 70,
      evidence: "Finance ARR export Q2",
      deletedAt: null,
    },
    create: {
      id: "seed-kr-revenue",
      organizationId,
      objectiveId: "seed-obj-company",
      title: "Retainer ARR",
      metricType: MetricType.CURRENCY,
      baseline: 8000000,
      target: 12000000,
      currentValue: 9800000,
      unit: "INR",
      progressPct: 45,
      ownerUserId: adminUserId,
      updateFrequency: "MONTHLY",
      confidenceScore: 70,
      evidence: "Finance ARR export Q2",
    },
  });

  await prisma.keyResultUpdate.deleteMany({
    where: { keyResultId: "seed-kr-revenue" },
  });
  await prisma.keyResultUpdate.createMany({
    data: [
      {
        id: "seed-kr-upd-1",
        organizationId,
        keyResultId: "seed-kr-revenue",
        previousValue: 8000000,
        newValue: 9000000,
        previousProgressPct: 0,
        progressPct: 25,
        note: "Month 1 update",
        createdById: adminUserId,
      },
      {
        id: "seed-kr-upd-2",
        organizationId,
        keyResultId: "seed-kr-revenue",
        previousValue: 9000000,
        newValue: 9800000,
        previousProgressPct: 25,
        progressPct: 45,
        note: "Month 2 update",
        evidence: "Finance ARR export Q2",
        createdById: adminUserId,
      },
    ],
  });

  await prisma.keyResult.upsert({
    where: { id: "seed-kr-winrate" },
    update: {
      organizationId,
      objectiveId: "seed-obj-sales",
      title: "Win rate",
      metricType: MetricType.PERCENT,
      baseline: 22,
      target: 35,
      currentValue: 28,
      unit: "%",
      progressPct: 46,
      ownerUserId: salesperson.user.id,
      updateFrequency: "WEEKLY",
      confidenceScore: 55,
      deletedAt: null,
    },
    create: {
      id: "seed-kr-winrate",
      organizationId,
      objectiveId: "seed-obj-sales",
      title: "Win rate",
      metricType: MetricType.PERCENT,
      baseline: 22,
      target: 35,
      currentValue: 28,
      unit: "%",
      progressPct: 46,
      ownerUserId: salesperson.user.id,
      updateFrequency: "WEEKLY",
      confidenceScore: 55,
    },
  });

  const healthRules = [
    {
      id: "seed-health-green",
      name: "On track",
      health: HealthStatus.GREEN,
      match: { minProgress: 70, maxDaysOverdue: 0, statuses: ["IN_PROGRESS"] },
      sortOrder: 1,
    },
    {
      id: "seed-health-amber",
      name: "At risk",
      health: HealthStatus.AMBER,
      match: {
        minProgress: 40,
        maxProgress: 69,
        maxDaysOverdue: 7,
        statuses: ["IN_PROGRESS", "AT_RISK"],
      },
      sortOrder: 2,
    },
    {
      id: "seed-health-red",
      name: "Off track",
      health: HealthStatus.RED,
      match: {
        maxProgress: 39,
        statuses: ["IN_PROGRESS", "AT_RISK", "BLOCKED"],
      },
      sortOrder: 3,
    },
    {
      id: "seed-health-grey",
      name: "Not started",
      health: HealthStatus.GREY,
      match: { statuses: ["NOT_STARTED"], requireStarted: false },
      sortOrder: 4,
    },
  ];
  for (const rule of healthRules) {
    await prisma.progressHealthRule.upsert({
      where: { id: rule.id },
      update: {
        organizationId,
        name: rule.name,
        health: rule.health,
        match: rule.match,
        sortOrder: rule.sortOrder,
        isActive: true,
      },
      create: {
        id: rule.id,
        organizationId,
        name: rule.name,
        health: rule.health,
        match: rule.match,
        sortOrder: rule.sortOrder,
      },
    });
  }

  // Configurable department scorecards (different KPI sets)
  async function seedScorecard(
    dept: { id: string; code?: string },
    codePrefix: string,
    name: string,
    defs: Array<{ code: string; name: string; category: string; unit?: string; value?: number }>,
  ) {
    const kpiIds: string[] = [];
    for (const def of defs) {
      const kpi = await prisma.kPI.upsert({
        where: {
          organizationId_code: {
            organizationId,
            code: `${codePrefix}_${def.code}`,
          },
        },
        update: {
          name: def.name,
          category: def.category,
          unit: def.unit ?? null,
          departmentId: dept.id,
          isActive: true,
          deletedAt: null,
        },
        create: {
          organizationId,
          departmentId: dept.id,
          name: def.name,
          code: `${codePrefix}_${def.code}`,
          category: def.category,
          unit: def.unit ?? null,
        },
      });
      kpiIds.push(kpi.id);
      if (def.value != null) {
        const periodStart = new Date(Date.UTC(2026, 3, 1));
        const periodEnd = new Date(Date.UTC(2026, 5, 30));
        await prisma.kPIValue.upsert({
          where: {
            kpiId_periodStart_periodEnd: {
              kpiId: kpi.id,
              periodStart,
              periodEnd,
            },
          },
          update: { value: def.value },
          create: {
            organizationId,
            kpiId: kpi.id,
            periodStart,
            periodEnd,
            value: def.value,
            createdById: adminUserId,
          },
        });
      }
    }

    const scorecard = await prisma.departmentScorecard.upsert({
      where: {
        organizationId_departmentId_name: {
          organizationId,
          departmentId: dept.id,
          name,
        },
      },
      update: { isActive: true, deletedAt: null },
      create: {
        organizationId,
        departmentId: dept.id,
        name,
        description: `${name} demo scorecard`,
      },
    });
    await prisma.scorecardKpi.deleteMany({ where: { scorecardId: scorecard.id } });
    for (const [index, kpiId] of kpiIds.entries()) {
      await prisma.scorecardKpi.create({
        data: { scorecardId: scorecard.id, kpiId, sortOrder: index },
      });
    }
  }

  await seedScorecard(departments.sales, "SAL", "FY scorecard", [
    { code: "LEAD_GEN", name: "Lead generation", category: "pipeline", value: 42 },
    { code: "PIPELINE_VALUE", name: "Pipeline", category: "pipeline", unit: "INR", value: 4500000 },
    { code: "CLOSED_REVENUE", name: "Closed revenue", category: "revenue", unit: "INR", value: 1800000 },
    { code: "CONVERSION_RATE", name: "Conversion rate", category: "funnel", unit: "%", value: 28 },
  ]);
  await seedScorecard(departments.creative, "CRV", "FY scorecard", [
    { code: "DESIGN_DELIVERABLES", name: "Design deliverables", category: "delivery", value: 18 },
    { code: "REVISION_RATE", name: "Revision rate", category: "quality", unit: "%", value: 12 },
    { code: "UTILIZATION", name: "Utilization", category: "capacity", unit: "%", value: 78 },
  ]);
  await seedScorecard(departments.hr, "HR", "FY scorecard", [
    { code: "OPEN_POSITIONS", name: "Open positions", category: "hiring", value: 3 },
    { code: "TIME_TO_HIRE", name: "Time to hire", category: "hiring", unit: "days", value: 34 },
    { code: "ATTRITION", name: "Attrition", category: "people", unit: "%", value: 6 },
  ]);
  await seedScorecard(departments.finance, "FIN", "FY scorecard", [
    { code: "INVOICE_COLLECTION", name: "Invoice collection", category: "cash", unit: "%", value: 88 },
    { code: "OVERDUE_INVOICES", name: "Overdue invoices", category: "cash", value: 4 },
    { code: "PROJECT_PROFITABILITY", name: "Project profitability", category: "margin", unit: "%", value: 32 },
  ]);

  await prisma.progressUpdate.deleteMany({
    where: { id: { startsWith: "seed-prog-upd-" } },
  });
  await prisma.progressUpdate.create({
    data: {
      id: "seed-prog-upd-1",
      organizationId,
      objectiveId: "seed-obj-sales",
      cadence: "WEEKLY",
      periodStart: new Date(Date.UTC(2026, 6, 7)),
      periodEnd: new Date(Date.UTC(2026, 6, 13)),
      body: "Pipeline coverage improved; two enterprise proposals out.",
      progressPct: 48,
      confidenceScore: 60,
      riskFlag: false,
      reviewStatus: "REVIEWED",
      reviewedById: adminUserId,
      reviewedAt: new Date(),
      createdById: salesperson.user.id,
    },
  });

  await prisma.decisionLog.upsert({
    where: { id: "seed-decision-1" },
    update: {
      organizationId,
      title: "Prioritize retainer expansion",
      decision: "Focus Q2 sales capacity on expansion motions over net-new SMB.",
      decidedById: adminUserId,
      deletedAt: null,
    },
    create: {
      id: "seed-decision-1",
      organizationId,
      title: "Prioritize retainer expansion",
      decision: "Focus Q2 sales capacity on expansion motions over net-new SMB.",
      decidedById: adminUserId,
    },
  });

  await prisma.businessReview.upsert({
    where: { id: "seed-review-q2" },
    update: {
      organizationId,
      title: "Q2 monthly leadership review",
      reviewType: "MONTHLY",
      periodStart: new Date(Date.UTC(2026, 5, 1)),
      periodEnd: new Date(Date.UTC(2026, 5, 30)),
      summary: "Retainer growth on track; delivery health green; hiring still open.",
      majorWins: "Closed Northstar expansion\nCollected overdue invoices",
      missedTargets: "Win rate still below 35%",
      snapshot: {
        capturedAt: new Date().toISOString(),
        objectives: [
          {
            id: "seed-obj-company",
            title: "Grow retainer revenue",
            progressPct: 62,
            health: "AMBER",
            status: "IN_PROGRESS",
          },
        ],
        kpis: [],
        risks: [],
      },
      createdById: adminUserId,
      deletedAt: null,
    },
    create: {
      id: "seed-review-q2",
      organizationId,
      title: "Q2 monthly leadership review",
      reviewType: "MONTHLY",
      periodStart: new Date(Date.UTC(2026, 5, 1)),
      periodEnd: new Date(Date.UTC(2026, 5, 30)),
      summary: "Retainer growth on track; delivery health green; hiring still open.",
      majorWins: "Closed Northstar expansion\nCollected overdue invoices",
      missedTargets: "Win rate still below 35%",
      snapshot: {
        capturedAt: new Date().toISOString(),
        objectives: [
          {
            id: "seed-obj-company",
            title: "Grow retainer revenue",
            progressPct: 62,
            health: "AMBER",
            status: "IN_PROGRESS",
          },
        ],
        kpis: [],
        risks: [],
      },
      createdById: adminUserId,
      items: {
        create: [
          {
            organizationId,
            itemType: "ACTION",
            title: "Coach sales on enterprise discovery",
            ownerUserId: salesperson.user.id,
            dueDate: new Date(Date.UTC(2026, 6, 31)),
            sortOrder: 0,
          },
          {
            organizationId,
            itemType: "RISK",
            title: "Designer bandwidth",
            sortOrder: 1,
          },
          {
            organizationId,
            itemType: "DECISION",
            title: "Prioritize retainer expansion",
            sortOrder: 2,
          },
        ],
      },
    },
  });

  await prisma.riskRegister.upsert({
    where: { id: "seed-risk-1" },
    update: {
      organizationId,
      title: "Key designer bandwidth",
      status: "OPEN",
      likelihood: 3,
      impact: 4,
      deletedAt: null,
    },
    create: {
      id: "seed-risk-1",
      organizationId,
      title: "Key designer bandwidth",
      status: "OPEN",
      likelihood: 3,
      impact: 4,
      ownerUserId: manager.user.id,
    },
  });

  const approval = await prisma.approvalRequest.upsert({
    where: { id: "seed-approval-1" },
    update: {
      organizationId,
      entityType: "Expense",
      entityId: "seed-expense-1",
      title: "Approve print samples expense",
      status: "PENDING",
      requestedById: employeeUser.user.id,
      deletedAt: null,
    },
    create: {
      id: "seed-approval-1",
      organizationId,
      entityType: "Expense",
      entityId: "seed-expense-1",
      title: "Approve print samples expense",
      status: "PENDING",
      requestedById: employeeUser.user.id,
    },
  });

  await prisma.approvalStep.deleteMany({ where: { requestId: approval.id } });
  await prisma.approvalStep.create({
    data: {
      organizationId,
      requestId: approval.id,
      stepOrder: 1,
      approverUserId: manager.user.id,
      status: "PENDING",
    },
  });

  const fy = await prisma.financialYear.findFirstOrThrow({
    where: { organizationId, code: "FY2026-27" },
  });

  const cycle = await prisma.xYMECycle.upsert({
    where: {
      organizationId_financialYearId_quarter: {
        organizationId,
        financialYearId: fy.id,
        quarter: 1,
      },
    },
    update: {
      name: "FY26 Q1",
      startDate: new Date("2026-04-01"),
      endDate: new Date("2026-06-30"),
      isActive: true,
      deletedAt: null,
    },
    create: {
      organizationId,
      financialYearId: fy.id,
      quarter: 1,
      name: "FY26 Q1",
      startDate: new Date("2026-04-01"),
      endDate: new Date("2026-06-30"),
      isActive: true,
    },
  });

  const plan = await prisma.xYMEPlan.upsert({
    where: {
      cycleId_employeeId: {
        cycleId: cycle.id,
        employeeId: employeeUser.employee.id,
      },
    },
    update: {
      organizationId,
      userId: employeeUser.user.id,
      status: "APPROVED",
      deletedAt: null,
    },
    create: {
      organizationId,
      cycleId: cycle.id,
      employeeId: employeeUser.employee.id,
      userId: employeeUser.user.id,
      status: "APPROVED",
      submittedAt: monthStart,
    },
  });

  await prisma.xYMEGoal.deleteMany({ where: { planId: plan.id } });
  await prisma.xYMEGoal.create({
    data: {
      organizationId,
      planId: plan.id,
      title: "Ship brand system v1",
      category: XYMECategory.X,
      progressPct: 55,
      status: ProgressStatus.IN_PROGRESS,
      dueDate: new Date(today.getTime() + 20 * 86400000),
      approvalStatus: "APPROVED",
    },
  });

  await prisma.xYMEApproval.deleteMany({ where: { planId: plan.id } });
  await prisma.xYMEApproval.create({
    data: {
      organizationId,
      planId: plan.id,
      status: "PENDING",
      reviewerId: manager.user.id,
      comment: "Need clearer evidence links",
    },
  });

  const salesTarget = await prisma.salesTarget.upsert({
    where: { id: "seed-sales-target" },
    update: {
      organizationId,
      employeeId: salesperson.employee.id,
      financialYearId: fy.id,
      month: monthStart,
      targetMinor: 50000000,
      deletedAt: null,
    },
    create: {
      id: "seed-sales-target",
      organizationId,
      employeeId: salesperson.employee.id,
      financialYearId: fy.id,
      month: monthStart,
      targetMinor: 50000000,
    },
  });

  await prisma.salesAchievement.upsert({
    where: {
      employeeId_month: {
        employeeId: salesperson.employee.id,
        month: monthStart,
      },
    },
    update: {
      organizationId,
      targetId: salesTarget.id,
      achievedMinor: 18000000,
    },
    create: {
      organizationId,
      employeeId: salesperson.employee.id,
      targetId: salesTarget.id,
      month: monthStart,
      achievedMinor: 18000000,
    },
  });

  await prisma.activityFeed.deleteMany({
    where: { organizationId, id: { startsWith: "seed-activity-" } },
  });
  await prisma.activityFeed.createMany({
    data: [
      {
        id: "seed-activity-1",
        organizationId,
        actorId: salesperson.user.id,
        entityType: "Deal",
        entityId: openDeal.id,
        action: "UPDATED",
        summary: "Moved Northstar brand refresh to Negotiation",
      },
      {
        id: "seed-activity-2",
        organizationId,
        actorId: financeUser.user.id,
        entityType: "Invoice",
        entityId: invoicePaid.id,
        action: "PAID",
        summary: "Marked DP-INV-2001 as paid",
      },
      {
        id: "seed-activity-3",
        organizationId,
        actorId: manager.user.id,
        entityType: "Project",
        entityId: project.id,
        action: "STATUS",
        summary: "Flagged Atlas migration as at risk",
      },
    ],
  });

  return {
    users: {
      manager: manager.user.email,
      sales: salesperson.user.email,
      finance: financeUser.user.email,
      hr: hrUser.user.email,
      employee: employeeUser.user.email,
    },
  };
}
