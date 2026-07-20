export {
  normalizeEmail,
  normalizePhone,
  normalizeCompanyName,
  normalizeDomain,
  daysSince,
  splitPersonName,
} from "./normalize";
export {
  scoreLead,
  DEFAULT_SCORING_RULES,
  type ScoreBreakdownItem,
  type LeadScoringInput,
  type ScoringFactor,
} from "./scoring";
export {
  findDuplicateHits,
  validateStageEntry,
  isStale,
  type DuplicateHit,
  type DuplicateMatchType,
} from "./duplicates";
export {
  leadCreateSchema,
  leadUpdateSchema,
  stageMoveSchema,
  bulkAssignSchema,
  bulkStageSchema,
  bulkTagsSchema,
  convertLeadSchema,
  followUpSchema,
  activitySchema,
} from "./schemas";
export {
  listLeads,
  getLeadDetail,
  createLead,
  updateLead,
  moveLeadStage,
  convertLead,
  listDuplicateReviews,
  reviewDuplicate,
  refreshDuplicateCandidates,
  getCrmLookups,
  computeAndPersistLeadScore,
} from "./leads";
export {
  logLeadActivity,
  createFollowUp,
  completeFollowUp,
  rescheduleFollowUp,
  listFollowUps,
  getFollowUpReminders,
  bulkAssignLeads,
  bulkChangeStage,
  bulkManageTags,
  getPipelineBoard,
  getSalespersonWorkload,
  getLeadActivityReport,
  createQuoteFromLead,
} from "./activities";
