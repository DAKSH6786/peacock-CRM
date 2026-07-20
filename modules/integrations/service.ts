import "server-only";

import type { Prisma } from "@prisma/client";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import { getJobQueue } from "@/jobs/queue";
import type { SessionUser } from "@/permissions/types";

import {
  generateApiKey,
  generateWebhookSigningSecret,
  hashApiKey,
  nextWebhookRetryAt,
  signWebhookPayload,
  verifyApiKey,
  isApiKeyUsable,
  type ApiKeyScope,
} from "./api-keys";

export async function createOrganizationApiKey(input: {
  user: SessionUser;
  organizationId: string;
  name: string;
  scopes: ApiKeyScope[];
  expiresAt?: Date | null;
}) {
  const generated = generateApiKey(
    process.env.NODE_ENV === "production" ? "live" : "test",
  );

  const record = await prisma.apiKey.create({
    data: {
      organizationId: input.organizationId,
      name: input.name,
      keyPrefix: generated.keyPrefix,
      keyHash: generated.keyHash,
      scopes: input.scopes,
      expiresAt: input.expiresAt ?? null,
      createdById: input.user.id,
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "ApiKey",
    entityId: record.id,
    metadata: { name: input.name, scopes: input.scopes, keyPrefix: generated.keyPrefix },
  });

  return { record, secret: generated.secret };
}

export async function revokeOrganizationApiKey(input: {
  user: SessionUser;
  organizationId: string;
  apiKeyId: string;
}) {
  const updated = await prisma.apiKey.updateMany({
    where: {
      id: input.apiKeyId,
      organizationId: input.organizationId,
      revokedAt: null,
    },
    data: {
      revokedAt: new Date(),
      revokedById: input.user.id,
    },
  });

  if (updated.count > 0) {
    await createAuditLog({
      organizationId: input.organizationId,
      actorId: input.user.id,
      action: "DELETE",
      entityType: "ApiKey",
      entityId: input.apiKeyId,
    });
  }

  return updated.count > 0;
}

export async function authenticateApiKey(
  secret: string,
  organizationId?: string,
) {
  const prefix = secret.slice(0, 12);
  const candidates = await prisma.apiKey.findMany({
    where: {
      keyPrefix: prefix,
      ...(organizationId ? { organizationId } : {}),
      revokedAt: null,
    },
    take: 10,
  });

  for (const candidate of candidates) {
    if (!verifyApiKey(secret, candidate.keyHash)) continue;
    if (!isApiKeyUsable(candidate)) continue;

    await prisma.apiKey.update({
      where: { id: candidate.id },
      data: { lastUsedAt: new Date() },
    });

    return candidate;
  }

  return null;
}

export async function createWebhookEndpoint(input: {
  user: SessionUser;
  organizationId: string;
  name: string;
  url: string;
  events: string[];
}) {
  const { secret, secretHash } = generateWebhookSigningSecret();

  const endpoint = await prisma.webhookEndpoint.create({
    data: {
      organizationId: input.organizationId,
      name: input.name,
      url: input.url,
      secretHash,
      events: input.events,
      isActive: true,
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "WebhookEndpoint",
    entityId: endpoint.id,
    metadata: { name: input.name, events: input.events },
  });

  return { endpoint, signingSecret: secret };
}

export async function enqueueWebhookDelivery(input: {
  organizationId: string;
  endpointId: string;
  event: string;
  payload: Record<string, unknown>;
}) {
  const delivery = await prisma.webhookDelivery.create({
    data: {
      organizationId: input.organizationId,
      endpointId: input.endpointId,
      event: input.event,
      payload: input.payload as Prisma.InputJsonValue,
      status: "PENDING",
    },
  });

  await getJobQueue().enqueue("deliver-webhook", {
    deliveryId: delivery.id,
  });

  return delivery;
}

/**
 * Delivery runner — records attempts/failures. Live HTTP post is gated on
 * active endpoints; signing uses the secret only when supplied by the caller
 * (secrets are never re-read from plaintext storage).
 */
export async function attemptWebhookDelivery(input: {
  deliveryId: string;
  signingSecret?: string;
}) {
  const delivery = await prisma.webhookDelivery.findUnique({
    where: { id: input.deliveryId },
    include: { endpoint: true },
  });
  if (!delivery || !delivery.endpoint.isActive) return;

  const attempts = delivery.attempts + 1;
  const payload = JSON.stringify(delivery.payload);
  const signature = input.signingSecret
    ? signWebhookPayload(input.signingSecret, payload)
    : null;

  try {
    const response = await fetch(delivery.endpoint.url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(signature ? { "x-peacock-signature": signature } : {}),
        "x-peacock-event": delivery.event,
      },
      body: payload,
    });

    if (response.ok) {
      await prisma.webhookDelivery.update({
        where: { id: delivery.id },
        data: {
          status: "DELIVERED",
          attempts,
          responseCode: response.status,
          deliveredAt: new Date(),
          errorMessage: null,
        },
      });
      await prisma.webhookEndpoint.update({
        where: { id: delivery.endpointId },
        data: { lastDeliveredAt: new Date(), failureCount: 0 },
      });
      return;
    }

    const nextRetryAt = nextWebhookRetryAt(attempts);
    await prisma.webhookDelivery.update({
      where: { id: delivery.id },
      data: {
        status: nextRetryAt ? "FAILED_RETRY" : "FAILED",
        attempts,
        responseCode: response.status,
        responseBody: (await response.text()).slice(0, 2000),
        nextRetryAt,
        errorMessage: `HTTP ${response.status}`,
      },
    });
    await prisma.webhookEndpoint.update({
      where: { id: delivery.endpointId },
      data: { failureCount: { increment: 1 } },
    });
  } catch (error) {
    const nextRetryAt = nextWebhookRetryAt(attempts);
    await prisma.webhookDelivery.update({
      where: { id: delivery.id },
      data: {
        status: nextRetryAt ? "FAILED_RETRY" : "FAILED",
        attempts,
        nextRetryAt,
        errorMessage: error instanceof Error ? error.message : "Delivery failed",
      },
    });
    await prisma.webhookEndpoint.update({
      where: { id: delivery.endpointId },
      data: { failureCount: { increment: 1 } },
    });
  }
}

export { hashApiKey };
