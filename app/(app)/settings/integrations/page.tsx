import type { Metadata } from "next";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import {
  INTEGRATION_EXTENSION_POINTS,
} from "@/modules/integrations";
import { createCalendarProvider, calendarSyncSupportedEntityTypes } from "@/modules/calendar";
import { requirePermission } from "@/permissions";
import { prisma } from "@/database";

import { IntegrationsAdminPanel } from "@/components/integrations/integrations-admin-panel";

export const metadata: Metadata = {
  title: "Integrations",
};

export default async function IntegrationsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "settings:manage");

  const organizationId = user!.organizationId!;
  const [apiKeys, webhooks, calendarConnections, emailLogs] = await Promise.all([
    prisma.apiKey.findMany({
      where: { organizationId },
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        name: true,
        keyPrefix: true,
        scopes: true,
        expiresAt: true,
        revokedAt: true,
        lastUsedAt: true,
        createdAt: true,
      },
    }),
    prisma.webhookEndpoint.findMany({
      where: { organizationId, deletedAt: null },
      include: { deliveries: { orderBy: { createdAt: "desc" }, take: 5 } },
      orderBy: { createdAt: "desc" },
    }),
    prisma.calendarConnection.findMany({ where: { organizationId } }),
    prisma.emailSendLog.findMany({
      where: { organizationId },
      orderBy: { createdAt: "desc" },
      take: 10,
    }),
  ]);

  const google = createCalendarProvider("google");
  const microsoft = createCalendarProvider("microsoft");

  return (
    <div>
      <PageHeader
        title="Integrations"
        description="API keys, webhooks, email/calendar adapters, and optional extension points. Secrets are hashed or vault-referenced — never committed."
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Calendar adapters</CardTitle>
            <CardDescription>
              Google Calendar and Microsoft Outlook are prepared. Sync is not
              claimed until credentials and an integration test succeed.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              Google: {google.isConfigured() ? "configured" : "disconnected"} ·
              Microsoft:{" "}
              {microsoft.isConfigured() ? "configured" : "disconnected"}
            </p>
            <p className="text-[var(--muted)]">
              Future sync entities:{" "}
              {calendarSyncSupportedEntityTypes().join(", ")}
            </p>
            {calendarConnections.length === 0 ? (
              <p className="text-[var(--muted)]">No calendar connections stored.</p>
            ) : (
              calendarConnections.map((conn) => (
                <p key={conn.id}>
                  {conn.provider}: {conn.status}
                  {conn.accountEmail ? ` · ${conn.accountEmail}` : ""}
                </p>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Extension points</CardTitle>
            <CardDescription>
              Contracts live in <code>docs/integrations.md</code>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {INTEGRATION_EXTENSION_POINTS.map((point) => (
              <div key={point.id}>
                <p className="font-medium">{point.label}</p>
                <p className="text-[var(--muted)]">{point.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <IntegrationsAdminPanel
        apiKeys={apiKeys.map((k) => ({
          ...k,
          expiresAt: k.expiresAt?.toISOString() ?? null,
          revokedAt: k.revokedAt?.toISOString() ?? null,
          lastUsedAt: k.lastUsedAt?.toISOString() ?? null,
          createdAt: k.createdAt.toISOString(),
        }))}
        webhooks={webhooks.map((w) => ({
          id: w.id,
          name: w.name,
          url: w.url,
          events: w.events,
          isActive: w.isActive,
          failureCount: w.failureCount,
          deliveries: w.deliveries.map((d) => ({
            id: d.id,
            event: d.event,
            status: d.status,
            attempts: d.attempts,
            createdAt: d.createdAt.toISOString(),
          })),
        }))}
        emailLogs={emailLogs.map((log) => ({
          id: log.id,
          provider: log.provider,
          toAddress: log.toAddress,
          subject: log.subject,
          status: log.status,
          previewMode: log.previewMode,
          createdAt: log.createdAt.toISOString(),
        }))}
      />
    </div>
  );
}
