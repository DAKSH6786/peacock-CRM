import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";

type ModulePlaceholderProps = {
  title: string;
  description: string;
  emptyTitle?: string;
  emptyDescription?: string;
  actions?: React.ReactNode;
};

export function ModulePlaceholder({
  title,
  description,
  emptyTitle = "No records yet",
  emptyDescription = "Connect this module to the service layer and seed data to populate live records.",
  actions,
}: ModulePlaceholderProps) {
  return (
    <div>
      <PageHeader title={title} description={description} actions={actions} />
      <EmptyState title={emptyTitle} description={emptyDescription} />
    </div>
  );
}
