"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { API_KEY_SCOPES } from "@/modules/integrations/api-keys";

type ApiKeyRow = {
  id: string;
  name: string;
  keyPrefix: string;
  scopes: string[];
  expiresAt: string | null;
  revokedAt: string | null;
  lastUsedAt: string | null;
  createdAt: string;
};

type WebhookRow = {
  id: string;
  name: string;
  url: string;
  events: string[];
  isActive: boolean;
  failureCount: number;
  deliveries: Array<{
    id: string;
    event: string;
    status: string;
    attempts: number;
    createdAt: string;
  }>;
};

type EmailLogRow = {
  id: string;
  provider: string;
  toAddress: string;
  subject: string;
  status: string;
  previewMode: boolean;
  createdAt: string;
};

type Props = {
  apiKeys: ApiKeyRow[];
  webhooks: WebhookRow[];
  emailLogs: EmailLogRow[];
};

export function IntegrationsAdminPanel({
  apiKeys: initialKeys,
  webhooks: initialWebhooks,
  emailLogs,
}: Props) {
  const [apiKeys, setApiKeys] = useState(initialKeys);
  const [webhooks, setWebhooks] = useState(initialWebhooks);
  const [secretOnce, setSecretOnce] = useState<string | null>(null);
  const [webhookSecretOnce, setWebhookSecretOnce] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function createKey() {
    const response = await fetch("/api/integrations/api-keys", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        action: "create",
        name: `Key ${new Date().toISOString().slice(0, 10)}`,
        scopes: ["read:crm", "imports:write"],
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error);
      return;
    }
    setSecretOnce(data.secret);
    setApiKeys((prev) => [
      {
        id: data.key.id,
        name: data.key.name,
        keyPrefix: data.key.keyPrefix,
        scopes: data.key.scopes,
        expiresAt: null,
        revokedAt: null,
        lastUsedAt: null,
        createdAt: new Date().toISOString(),
      },
      ...prev,
    ]);
  }

  async function revokeKey(apiKeyId: string) {
    const response = await fetch("/api/integrations/api-keys", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "revoke", apiKeyId }),
    });
    if (response.ok) {
      setApiKeys((prev) =>
        prev.map((k) =>
          k.id === apiKeyId ? { ...k, revokedAt: new Date().toISOString() } : k,
        ),
      );
    }
  }

  async function createWebhook() {
    const response = await fetch("/api/integrations/webhooks", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: "Lead intake",
        url: "https://example.com/hooks/peacock",
        events: ["lead.created", "deal.won"],
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error);
      return;
    }
    setWebhookSecretOnce(data.signingSecret);
    setWebhooks((prev) => [
      {
        id: data.endpoint.id,
        name: data.endpoint.name,
        url: data.endpoint.url,
        events: data.endpoint.events,
        isActive: data.endpoint.isActive,
        failureCount: 0,
        deliveries: [],
      },
      ...prev,
    ]);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>API keys</CardTitle>
          <CardDescription>
            Hashed storage, scopes, expiry, revocation, last-used. Secret shown
            once. Available scopes: {API_KEY_SCOPES.join(", ")}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button type="button" onClick={() => void createKey()}>
            Create API key
          </Button>
          {secretOnce ? (
            <p className="rounded-md bg-[var(--surface-2)] p-3 text-xs break-all">
              Copy now — plaintext secret will not be shown again:
              <br />
              {secretOnce}
            </p>
          ) : null}
          {apiKeys.map((key) => (
            <div
              key={key.id}
              className="flex items-start justify-between gap-2 border-b border-[var(--border)] pb-2"
            >
              <div>
                <p className="font-medium">
                  {key.name}{" "}
                  <span className="text-xs text-[var(--muted)]">
                    {key.keyPrefix}…
                  </span>
                </p>
                <p className="text-xs text-[var(--muted)]">
                  {key.scopes.join(", ")}
                  {key.revokedAt ? " · revoked" : ""}
                  {key.lastUsedAt
                    ? ` · last used ${key.lastUsedAt.slice(0, 10)}`
                    : ""}
                </p>
              </div>
              {!key.revokedAt ? (
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => void revokeKey(key.id)}
                >
                  Revoke
                </Button>
              ) : null}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Webhooks</CardTitle>
          <CardDescription>
            Signing secrets, delivery logs, retries, and failure tracking.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button type="button" variant="secondary" onClick={() => void createWebhook()}>
            Create webhook endpoint
          </Button>
          {webhookSecretOnce ? (
            <p className="rounded-md bg-[var(--surface-2)] p-3 text-xs break-all">
              Signing secret (once): {webhookSecretOnce}
            </p>
          ) : null}
          {webhooks.map((hook) => (
            <div key={hook.id} className="border-b border-[var(--border)] pb-2">
              <p className="font-medium">
                {hook.name}{" "}
                <span className="text-xs text-[var(--muted)]">
                  {hook.isActive ? "active" : "inactive"} · failures{" "}
                  {hook.failureCount}
                </span>
              </p>
              <p className="text-xs text-[var(--muted)]">{hook.url}</p>
              <p className="text-xs text-[var(--muted)]">
                {hook.events.join(", ")}
              </p>
              {hook.deliveries.slice(0, 3).map((d) => (
                <p key={d.id} className="text-xs">
                  {d.event} · {d.status} · attempt {d.attempts}
                </p>
              ))}
            </div>
          ))}
          {message ? <p className="text-sm">{message}</p> : null}
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Email send log</CardTitle>
          <CardDescription>
            Provider-neutral delivery with preview mode in development.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {emailLogs.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No sends yet.</p>
          ) : (
            emailLogs.map((log) => (
              <p key={log.id} className="text-sm">
                {log.createdAt.slice(0, 19)} · {log.provider} · {log.status}
                {log.previewMode ? " (preview)" : ""} · {log.toAddress} ·{" "}
                {log.subject}
              </p>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
