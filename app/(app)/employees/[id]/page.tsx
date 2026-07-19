import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Employee profile",
};

type EmployeePageProps = {
  params: Promise<{ id: string }>;
};

export default async function EmployeePage({ params }: EmployeePageProps) {
  const { id } = await params;

  return (
    <ModulePlaceholder
      title="Employee profile"
      description={`Individual employee record and activity for ID ${id}.`}
      emptyTitle="Employee not loaded"
      emptyDescription="Wire this route to the employees service layer to load a real profile from the database."
    />
  );
}
