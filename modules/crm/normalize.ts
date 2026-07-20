export function normalizeEmail(email?: string | null): string | null {
  if (!email) return null;
  const value = email.trim().toLowerCase();
  return value.includes("@") ? value : null;
}

export function normalizePhone(phone?: string | null): string | null {
  if (!phone) return null;
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 7 ? digits : null;
}

export function normalizeCompanyName(name?: string | null): string | null {
  if (!name) return null;
  const value = name
    .trim()
    .toLowerCase()
    .replace(/\b(ltd|llc|inc|pvt|private|limited|co|company)\b\.?/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
  return value || null;
}

export function normalizeDomain(
  websiteOrEmail?: string | null,
): string | null {
  if (!websiteOrEmail) return null;
  let value = websiteOrEmail.trim().toLowerCase();
  if (value.includes("@")) {
    value = value.split("@")[1] ?? "";
  }
  value = value
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .split("/")[0]
    ?.trim() ?? "";
  return value.includes(".") ? value : null;
}

export function daysSince(date: Date | string | null | undefined, now = new Date()): number | null {
  if (!date) return null;
  const d = typeof date === "string" ? new Date(date) : date;
  if (Number.isNaN(d.getTime())) return null;
  return Math.max(0, Math.floor((now.getTime() - d.getTime()) / 86_400_000));
}

export function splitPersonName(fullName: string): {
  firstName: string;
  lastName: string | null;
} {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return { firstName: "Unknown", lastName: null };
  if (parts.length === 1) return { firstName: parts[0]!, lastName: null };
  return {
    firstName: parts[0]!,
    lastName: parts.slice(1).join(" "),
  };
}
