import {
  normalizeCompanyName,
  normalizeDomain,
  normalizeEmail,
  normalizePhone,
} from "./normalize";

export type DuplicateMatchType = "EMAIL" | "PHONE" | "DOMAIN" | "COMPANY";

export type LeadIdentity = {
  id: string;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  companyName?: string | null;
  normalizedEmail?: string | null;
  normalizedPhone?: string | null;
  normalizedCompany?: string | null;
  normalizedDomain?: string | null;
};

export type DuplicateHit = {
  leadId: string;
  matchLeadId: string;
  matchType: DuplicateMatchType;
  matchValue: string;
};

function identityKeys(lead: LeadIdentity) {
  return {
    email: lead.normalizedEmail ?? normalizeEmail(lead.email),
    phone: lead.normalizedPhone ?? normalizePhone(lead.phone),
    company:
      lead.normalizedCompany ?? normalizeCompanyName(lead.companyName),
    domain:
      lead.normalizedDomain ??
      normalizeDomain(lead.website) ??
      normalizeDomain(lead.email),
  };
}

/**
 * Find possible duplicates. Never merges — returns candidates for human review.
 */
export function findDuplicateHits(
  subject: LeadIdentity,
  pool: LeadIdentity[],
): DuplicateHit[] {
  const subjectKeys = identityKeys(subject);
  const hits: DuplicateHit[] = [];

  for (const other of pool) {
    if (other.id === subject.id) continue;
    const otherKeys = identityKeys(other);

    if (subjectKeys.email && subjectKeys.email === otherKeys.email) {
      hits.push({
        leadId: subject.id,
        matchLeadId: other.id,
        matchType: "EMAIL",
        matchValue: subjectKeys.email,
      });
    }
    if (subjectKeys.phone && subjectKeys.phone === otherKeys.phone) {
      hits.push({
        leadId: subject.id,
        matchLeadId: other.id,
        matchType: "PHONE",
        matchValue: subjectKeys.phone,
      });
    }
    if (subjectKeys.domain && subjectKeys.domain === otherKeys.domain) {
      hits.push({
        leadId: subject.id,
        matchLeadId: other.id,
        matchType: "DOMAIN",
        matchValue: subjectKeys.domain,
      });
    }
    if (subjectKeys.company && subjectKeys.company === otherKeys.company) {
      hits.push({
        leadId: subject.id,
        matchLeadId: other.id,
        matchType: "COMPANY",
        matchValue: subjectKeys.company,
      });
    }
  }

  return hits;
}

export type StageGateResult =
  | { ok: true }
  | { ok: false; missingFields: string[] };

export function validateStageEntry(
  lead: Record<string, unknown>,
  requiredFields: string[],
): StageGateResult {
  const missing = requiredFields.filter((field) => {
    const value = lead[field];
    if (value == null) return true;
    if (typeof value === "string" && value.trim() === "") return true;
    if (Array.isArray(value) && value.length === 0) return true;
    return false;
  });
  return missing.length === 0 ? { ok: true } : { ok: false, missingFields: missing };
}

export function isStale(
  enteredStageAt: Date | null | undefined,
  staleAfterDays: number | null | undefined,
  now = new Date(),
): boolean {
  if (!enteredStageAt || !staleAfterDays || staleAfterDays <= 0) return false;
  const ageDays =
    (now.getTime() - enteredStageAt.getTime()) / 86_400_000;
  return ageDays >= staleAfterDays;
}
