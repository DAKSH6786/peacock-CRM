import { z } from "zod";

export const leadCreateSchema = z.object({
  personName: z.string().min(1).max(200),
  companyName: z.string().max(200).optional().nullable(),
  email: z.string().email().optional().nullable().or(z.literal("")),
  phone: z.string().max(40).optional().nullable(),
  country: z.string().max(80).optional().nullable(),
  city: z.string().max(80).optional().nullable(),
  website: z.string().max(300).optional().nullable(),
  sourceId: z.string().optional().nullable(),
  statusId: z.string().optional().nullable(),
  pipelineId: z.string().optional().nullable(),
  stageId: z.string().optional().nullable(),
  campaignId: z.string().optional().nullable(),
  estimatedValueMinor: z.number().int().nonnegative().optional().nullable(),
  currencyCode: z.string().length(3).optional(),
  probability: z.number().int().min(0).max(100).optional().nullable(),
  expectedClosingDate: z.string().optional().nullable(),
  assignedUserId: z.string().optional().nullable(),
  nextFollowUpAt: z.string().datetime().optional().nullable(),
  interestedServices: z.array(z.string()).optional(),
  notes: z.string().max(5000).optional().nullable(),
  companySize: z.string().max(80).optional().nullable(),
  budgetMinor: z.number().int().nonnegative().optional().nullable(),
  decisionTimeline: z.string().max(80).optional().nullable(),
  websiteQuality: z.number().int().min(0).max(10).optional().nullable(),
  existingRelationship: z.boolean().optional(),
  tagIds: z.array(z.string()).optional(),
});

export const leadUpdateSchema = leadCreateSchema.partial().extend({
  lostReasonId: z.string().optional().nullable(),
});

export const stageMoveSchema = z.object({
  stageId: z.string().min(1),
  note: z.string().max(1000).optional(),
  lostReasonId: z.string().optional().nullable(),
  confirmClose: z.boolean().optional(),
});

export const bulkAssignSchema = z.object({
  leadIds: z.array(z.string()).min(1),
  assignedUserId: z.string().nullable(),
  reason: z.string().max(500).optional(),
});

export const bulkStageSchema = z.object({
  leadIds: z.array(z.string()).min(1),
  stageId: z.string().min(1),
  lostReasonId: z.string().optional().nullable(),
  confirmClose: z.boolean().optional(),
});

export const bulkTagsSchema = z.object({
  leadIds: z.array(z.string()).min(1),
  tagIds: z.array(z.string()).min(1),
  mode: z.enum(["ADD", "REMOVE", "SET"]).default("ADD"),
});

export const convertLeadSchema = z.object({
  createContact: z.boolean().default(true),
  createCompany: z.boolean().default(true),
  createDeal: z.boolean().default(true),
  createClientAccount: z.boolean().default(true),
  createProjectPlaceholder: z.boolean().default(false),
  dealName: z.string().max(200).optional(),
  projectName: z.string().max(200).optional(),
});

export const followUpSchema = z.object({
  dueAt: z.string().datetime(),
  notes: z.string().max(2000).optional().nullable(),
  assignedUserId: z.string().optional().nullable(),
});

export const activitySchema = z.object({
  type: z.enum(["NOTE", "CALL", "MEETING", "EMAIL", "OTHER"]),
  subject: z.string().max(200).optional().nullable(),
  body: z.string().max(10000).optional().nullable(),
  occurredAt: z.string().datetime().optional(),
  direction: z.enum(["INBOUND", "OUTBOUND"]).optional(),
  durationSec: z.number().int().nonnegative().optional(),
  outcome: z.string().max(200).optional().nullable(),
  startsAt: z.string().datetime().optional(),
  endsAt: z.string().datetime().optional(),
  location: z.string().max(300).optional().nullable(),
});

export type LeadCreateInput = z.infer<typeof leadCreateSchema>;
export type LeadUpdateInput = z.infer<typeof leadUpdateSchema>;
export type ConvertLeadInput = z.infer<typeof convertLeadSchema>;
