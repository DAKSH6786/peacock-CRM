import { describe, expect, it } from "vitest";

import {
  apiKeyHasScope,
  generateApiKey,
  generateWebhookSigningSecret,
  hashApiKey,
  isApiKeyUsable,
  nextWebhookRetryAt,
  signWebhookPayload,
  verifyApiKey,
} from "@/modules/integrations/api-keys";

describe("api key security", () => {
  it("hashes secrets and never verifies wrong keys", () => {
    const generated = generateApiKey("test");
    expect(generated.secret.startsWith("pk_test_")).toBe(true);
    expect(generated.keyHash).toBe(hashApiKey(generated.secret));
    expect(verifyApiKey(generated.secret, generated.keyHash)).toBe(true);
    expect(verifyApiKey("pk_test_wrong", generated.keyHash)).toBe(false);
  });

  it("rejects revoked or expired keys", () => {
    expect(isApiKeyUsable({ revokedAt: new Date() })).toBe(false);
    expect(
      isApiKeyUsable({ expiresAt: new Date(Date.now() - 1000) }),
    ).toBe(false);
    expect(isApiKeyUsable({ expiresAt: new Date(Date.now() + 60_000) })).toBe(
      true,
    );
  });

  it("checks scopes explicitly", () => {
    expect(apiKeyHasScope(["read:crm"], "read:crm")).toBe(true);
    expect(apiKeyHasScope(["read:crm"], "write:crm")).toBe(false);
  });

  it("creates webhook signing secrets and signatures", () => {
    const { secret, secretHash } = generateWebhookSigningSecret();
    expect(secret.startsWith("whsec_")).toBe(true);
    expect(secretHash).toBe(hashApiKey(secret));
    const header = signWebhookPayload(secret, "{\"ok\":true}", 1_700_000_000);
    expect(header.startsWith("t=1700000000,v1=")).toBe(true);
  });

  it("schedules webhook retries with backoff and stops after max", () => {
    const first = nextWebhookRetryAt(1)!;
    const second = nextWebhookRetryAt(2)!;
    expect(second.getTime()).toBeGreaterThan(first.getTime());
    expect(nextWebhookRetryAt(5)).toBeNull();
  });
});
