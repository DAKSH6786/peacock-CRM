import { createHash, randomBytes } from "node:crypto";

export type ApiKeyScope =
  | "read:crm"
  | "write:crm"
  | "read:finance"
  | "write:finance"
  | "read:hr"
  | "webhooks:manage"
  | "imports:write"
  | "exports:read";

export const API_KEY_SCOPES: ApiKeyScope[] = [
  "read:crm",
  "write:crm",
  "read:finance",
  "write:finance",
  "read:hr",
  "webhooks:manage",
  "imports:write",
  "exports:read",
];

export type GeneratedApiKey = {
  /** Full secret shown once — never persist */
  secret: string;
  keyPrefix: string;
  keyHash: string;
};

export function generateApiKey(env: "live" | "test" = "live"): GeneratedApiKey {
  const raw = randomBytes(32).toString("base64url");
  const secret = `pk_${env}_${raw}`;
  const keyPrefix = secret.slice(0, 12);
  return {
    secret,
    keyPrefix,
    keyHash: hashApiKey(secret),
  };
}

export function hashApiKey(secret: string): string {
  return createHash("sha256").update(secret).digest("hex");
}

export function verifyApiKey(
  secret: string,
  storedHash: string,
): boolean {
  const incoming = hashApiKey(secret);
  if (incoming.length !== storedHash.length) return false;
  // timing-safe compare
  let mismatch = 0;
  for (let i = 0; i < incoming.length; i += 1) {
    mismatch |= incoming.charCodeAt(i) ^ storedHash.charCodeAt(i);
  }
  return mismatch === 0;
}

export function isApiKeyUsable(input: {
  revokedAt?: Date | null;
  expiresAt?: Date | null;
  now?: Date;
}): boolean {
  const now = input.now ?? new Date();
  if (input.revokedAt) return false;
  if (input.expiresAt && input.expiresAt.getTime() < now.getTime()) return false;
  return true;
}

export function apiKeyHasScope(
  scopes: string[],
  required: ApiKeyScope,
): boolean {
  return scopes.includes(required);
}

export function generateWebhookSigningSecret(): {
  secret: string;
  secretHash: string;
} {
  const secret = `whsec_${randomBytes(24).toString("base64url")}`;
  return { secret, secretHash: hashApiKey(secret) };
}

export function signWebhookPayload(
  secret: string,
  payload: string,
  timestamp = Math.floor(Date.now() / 1000),
): string {
  const body = `${timestamp}.${payload}`;
  const signature = createHash("sha256")
    .update(`${secret}.${body}`)
    .digest("hex");
  return `t=${timestamp},v1=${signature}`;
}

export function nextWebhookRetryAt(
  attempts: number,
  from = new Date(),
): Date | null {
  // attempts is count after failure; exponential backoff up to 5 retries
  if (attempts >= 5) return null;
  const minutes = Math.pow(2, attempts); // 2, 4, 8, 16, 32
  return new Date(from.getTime() + minutes * 60 * 1000);
}
