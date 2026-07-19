import type { Metadata } from "next";
import Link from "next/link";
import { BriefcaseBusiness, Goal, Landmark, Users } from "lucide-react";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Dashboard",
};

const modules = [
  {
    title: "CRM & pipeline",
    description: "Leads, contacts, companies, and deal stages.",
    href: "/crm",
    icon: BriefcaseBusiness,
    tone: "bg-[#b7c6c2]",
  },
  {
    title: "Delivery & XYME",
    description: "Projects, tasks, and goal cadence across teams.",
    href: "/xyme",
    icon: Goal,
    tone: "bg-[#ffe17c]",
  },
  {
    title: "People & finance",
    description: "HR, attendance, invoices, and approvals.",
    href: "/finance",
    icon: Landmark,
    tone: "bg-white",
  },
] as const;

export default async function DashboardPage() {
  const session = await auth();
  requirePermission(
    session?.user
      ? {
          id: session.user.id,
          email: session.user.email ?? "",
          name: session.user.name,
          organizationId: session.user.organizationId,
          role: session.user.role as never,
          status: session.user.status,
        }
      : null,
    "dashboard:view",
  );

  return (
    <div>
      <div className="mb-8 overflow-hidden rounded-xl border-2 border-black bg-[#ffe17c] shadow-[8px_8px_0_0_#000000]">
        <div className="bg-dot-pattern px-6 py-8 md:px-8">
          <Badge variant="white">NEW · PEACOCK ONE</Badge>
          <div className="mt-4">
            <PageHeader
              title="Command center"
              description="Operational overview for Digital Peacock. Module metrics populate from live services and the seed dataset."
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/crm/leads"
              className="inline-flex h-11 items-center justify-center rounded-[0.75rem] border-2 border-black bg-black px-5 text-sm font-bold text-white shadow-[8px_8px_0_0_#000000] transition-all duration-200 hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-[4px_4px_0_0_#000000]"
            >
              Open CRM
            </Link>
            <Link
              href="/approvals"
              className="inline-flex h-11 items-center justify-center rounded-[0.75rem] border-2 border-black bg-white px-5 text-sm font-bold text-black shadow-[4px_4px_0_0_#000000] transition-all duration-200 hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none"
            >
              Review approvals
            </Link>
          </div>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {modules.map((module) => {
          const Icon = module.icon;
          return (
            <Card
              key={module.title}
              className="transition-transform duration-200 hover:-translate-y-1"
            >
              <CardHeader>
                <span
                  className={`mb-3 flex h-16 w-16 items-center justify-center rounded-xl border-2 border-black ${module.tone} shadow-[4px_4px_0_0_#000000] transition-colors hover:bg-[#ffe17c]`}
                >
                  <Icon className="h-7 w-7" aria-hidden />
                </span>
                <CardTitle>{module.title}</CardTitle>
                <CardDescription>{module.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Link
                  href={module.href}
                  className="inline-flex items-center font-[family-name:var(--font-body)] text-sm font-bold underline decoration-2 underline-offset-4"
                >
                  Open module
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="mt-5 border-2 border-black bg-[#171e19] text-white shadow-[8px_8px_0_0_#000000]">
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-full border-4 border-[#b7c6c2] bg-[#272727]">
              <Users className="h-5 w-5 text-[#ffe17c]" aria-hidden />
            </span>
            <div>
              <CardTitle className="text-white">Team access</CardTitle>
              <CardDescription className="text-[#b7c6c2]">
                Roles and permissions are enforced server-side. Sensitive
                finance and compensation data stays gated.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
