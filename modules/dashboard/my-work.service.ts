import "server-only";

import { prisma } from "@/database";
import type { MyWorkPayload } from "@/modules/dashboard/my-work.types";
import type { SessionUser } from "@/permissions";
import { requireOrganization } from "@/permissions";

export type { MyWorkItem, MyWorkPayload } from "@/modules/dashboard/my-work.types";

export async function getMyWorkPayload(
  user: SessionUser,
): Promise<MyWorkPayload> {
  const authed = requireOrganization(user);
  const organizationId = authed.organizationId;
  const now = new Date();

  const employee = await prisma.employee.findFirst({
    where: { userId: authed.id, organizationId, deletedAt: null },
    select: { id: true },
  });

  const [
    tasks,
    deliverables,
    leadFollowUps,
    approvals,
    xymeGoals,
    checkIns,
    attendanceExceptions,
    announcements,
  ] = await Promise.all([
    prisma.task.findMany({
      where: {
        organizationId,
        deletedAt: null,
        assigneeId: authed.id,
        status: { notIn: ["DONE", "COMPLETED", "CANCELLED"] },
      },
      orderBy: { dueDate: "asc" },
      take: 20,
      select: { id: true, title: true, dueDate: true, status: true },
    }),
    prisma.deliverableApproval.findMany({
      where: {
        organizationId,
        status: "PENDING",
        reviewerId: authed.id,
      },
      take: 20,
      select: {
        id: true,
        deliverable: { select: { title: true, id: true } },
      },
    }),
    prisma.followUp.findMany({
      where: {
        organizationId,
        deletedAt: null,
        completedAt: null,
        OR: [{ assignedUserId: authed.id }, { lead: { assignedUserId: authed.id } }],
      },
      orderBy: { dueAt: "asc" },
      take: 20,
      select: {
        id: true,
        dueAt: true,
        notes: true,
        lead: { select: { id: true, personName: true } },
      },
    }),
    prisma.approvalRequest.findMany({
      where: {
        organizationId,
        deletedAt: null,
        status: "PENDING",
        OR: [
          { requestedById: authed.id },
          { steps: { some: { approverUserId: authed.id, status: "PENDING" } } },
        ],
      },
      take: 20,
      select: { id: true, title: true, status: true },
    }),
    employee
      ? prisma.xYMEGoal.findMany({
          where: {
            organizationId,
            deletedAt: null,
            plan: { employeeId: employee.id, deletedAt: null },
            status: { notIn: ["COMPLETED", "CANCELLED"] },
          },
          take: 20,
          select: {
            id: true,
            title: true,
            progressPct: true,
            category: true,
            dueDate: true,
          },
        })
      : Promise.resolve([]),
    employee
      ? prisma.xYMEPlan.findMany({
          where: {
            organizationId,
            employeeId: employee.id,
            deletedAt: null,
            status: { in: ["APPROVED", "PENDING"] },
            checkIns: { none: { checkedInAt: { gte: new Date(now.getTime() - 7 * 86400000) } } },
          },
          take: 10,
          select: { id: true, cycle: { select: { name: true } } },
        })
      : Promise.resolve([]),
    employee
      ? prisma.attendanceCorrectionRequest.findMany({
          where: {
            organizationId,
            employeeId: employee.id,
            status: "PENDING",
          },
          take: 10,
          select: { id: true, date: true, reason: true },
        })
      : Promise.resolve([]),
    prisma.announcement.findMany({
      where: {
        organizationId,
        deletedAt: null,
        OR: [{ publishedAt: null }, { publishedAt: { lte: now } }],
      },
      orderBy: { createdAt: "desc" },
      take: 10,
      select: { id: true, title: true, createdAt: true },
    }),
  ]);

  return {
    tasks: tasks.map((task) => ({
      id: task.id,
      title: task.title,
      meta: task.dueDate?.toISOString().slice(0, 10) ?? task.status,
      href: "/tasks",
    })),
    deliverables: deliverables.map((item) => ({
      id: item.id,
      title: item.deliverable.title,
      meta: "Awaiting your action",
      href: "/deliverables",
    })),
    leadFollowUps: leadFollowUps.map((item) => ({
      id: item.id,
      title: item.lead.personName,
      meta: item.dueAt.toISOString().slice(0, 10),
      href: `/crm/leads`,
    })),
    approvals: approvals.map((item) => ({
      id: item.id,
      title: item.title,
      meta: item.status,
      href: "/approvals",
    })),
    xymeGoals: xymeGoals.map((goal) => ({
      id: goal.id,
      title: `${goal.category}: ${goal.title}`,
      meta: `${goal.progressPct}%`,
      href: "/xyme",
    })),
    checkInReminders: checkIns.map((plan) => ({
      id: plan.id,
      title: `Check-in · ${plan.cycle.name}`,
      meta: "Due this week",
      href: "/xyme",
    })),
    attendanceExceptions: attendanceExceptions.map((item) => ({
      id: item.id,
      title: "Attendance correction",
      meta: `${item.date.toISOString().slice(0, 10)} · ${item.reason}`,
      href: "/hr/attendance",
    })),
    announcements: announcements.map((item) => ({
      id: item.id,
      title: item.title,
      meta: item.createdAt.toISOString().slice(0, 10),
      href: "/notifications",
    })),
  };
}
