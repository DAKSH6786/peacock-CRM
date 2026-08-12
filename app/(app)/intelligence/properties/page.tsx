import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { RunDemoButton } from "@/components/intelligence/run-demo-button";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import { listVisibilityProperties } from "@/modules/intelligence/service";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Visibility properties",
};

export default async function VisibilityPropertiesPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");
  const canRun = hasPermission(
    user!.role as MembershipRole | null,
    "intelligence:run",
  );
  const properties = await listVisibilityProperties(user!.organizationId!);

  return (
    <div>
      <PageHeader
        title="Visibility properties"
        description="Domains Peacock One crawls, probes, and continuously measures across SEO, AEO, and GEO."
        actions={
          <Button asChild variant="secondary">
            <Link href="/intelligence">Back to cockpit</Link>
          </Button>
        }
      />

      <div className="grid gap-4">
        {properties.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No properties yet</CardTitle>
              <CardDescription>
                Seed the database or create a property to begin observation.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          properties.map((property) => (
            <Card key={property.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle>{property.name}</CardTitle>
                  <CardDescription>
                    {property.primaryDomain} · {property.rootUrl}
                  </CardDescription>
                </div>
                {canRun ? <RunDemoButton propertyId={property.id} /> : null}
              </CardHeader>
              <CardContent className="flex gap-6 text-sm text-[var(--muted)]">
                <span>{property._count.intelligenceRuns} runs</span>
                <span>{property._count.recommendations} recommendations</span>
                <span>{property.industry ?? "Industry unset"}</span>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
