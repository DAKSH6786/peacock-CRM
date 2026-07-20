import type { PrismaClient } from "@prisma/client";
import {
  MembershipRole,
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
    { name: "Discovery", code: "DISC", sortOrder: 1, probability: 20 },
    { name: "Proposal", code: "PROP", sortOrder: 2, probability: 45 },
    { name: "Negotiation", code: "NEGO", sortOrder: 3, probability: 70 },
    {
      name: "Won",
      code: "WON",
      sortOrder: 4,
      probability: 100,
      isClosedWon: true,
    },
    {
      name: "Lost",
      code: "LOST",
      sortOrder: 5,
      probability: 0,
      isClosedLost: true,
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
        isClosedWon: "isClosedWon" in def ? def.isClosedWon : false,
        isClosedLost: "isClosedLost" in def ? def.isClosedLost : false,
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
      scope: OwnershipScope.COMPANY,
      progressPct: 62,
      status: ProgressStatus.IN_PROGRESS,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-company",
      organizationId,
      title: "Grow retainer revenue",
      scope: OwnershipScope.COMPANY,
      progressPct: 62,
      status: ProgressStatus.IN_PROGRESS,
      createdById: adminUserId,
    },
  });

  await prisma.objective.upsert({
    where: { id: "seed-obj-sales" },
    update: {
      organizationId,
      title: "Improve win rate",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.sales.id,
      progressPct: 48,
      status: ProgressStatus.IN_PROGRESS,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-sales",
      organizationId,
      title: "Improve win rate",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.sales.id,
      progressPct: 48,
      status: ProgressStatus.IN_PROGRESS,
      createdById: salesperson.user.id,
    },
  });

  await prisma.objective.upsert({
    where: { id: "seed-obj-ops" },
    update: {
      organizationId,
      title: "On-time delivery",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.operations.id,
      progressPct: 71,
      status: ProgressStatus.IN_PROGRESS,
      deletedAt: null,
    },
    create: {
      id: "seed-obj-ops",
      organizationId,
      title: "On-time delivery",
      scope: OwnershipScope.DEPARTMENT,
      departmentId: departments.operations.id,
      progressPct: 71,
      status: ProgressStatus.IN_PROGRESS,
      createdById: manager.user.id,
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
