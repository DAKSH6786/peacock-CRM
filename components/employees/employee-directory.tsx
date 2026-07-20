"use client";

import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable } from "@/components/shared/data-table";
import { AdvancedFilters } from "@/components/shared/filters";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type EmployeeRow = {
  id: string;
  code: string;
  name: string;
  department: string;
  status: string;
};

const columns: ColumnDef<EmployeeRow>[] = [
  { accessorKey: "code", header: "Code" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "department", header: "Department" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
];

export function EmployeeDirectory() {
  const [department, setDepartment] = useState("");
  const [status, setStatus] = useState("");
  const data = useMemo<EmployeeRow[]>(() => [], []);

  return (
    <div>
      <PageHeader
        title="Employee directory"
        description="Browse people records with search, filters, column controls, and permission-aware export."
        actions={<Button variant="secondary">Invite employee</Button>}
      />
      <AdvancedFilters
        fields={[
          {
            id: "department",
            label: "Department",
            value: department,
            onChange: setDepartment,
            placeholder: "All departments",
          },
          {
            id: "status",
            label: "Status",
            value: status,
            onChange: setStatus,
            placeholder: "All statuses",
          },
        ]}
        onClear={() => {
          setDepartment("");
          setStatus("");
        }}
        savedViews={[
          {
            id: "active",
            name: "Active only",
            onSelect: () => setStatus("ACTIVE"),
          },
        ]}
      />
      <DataTable
        columns={columns}
        data={data}
        searchKey="name"
        searchPlaceholder="Search employees…"
        enableRowSelection
        canExport={false}
        emptyTitle="No employees to display"
        emptyDescription="Employee rows load from the people service and seed data. Sensitive compensation fields never appear in this table."
        bulkActions={
          <Button size="sm" variant="outline">
            Assign manager
          </Button>
        }
      />
    </div>
  );
}
