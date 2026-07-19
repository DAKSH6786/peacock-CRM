import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type ModulePlaceholderProps = {
  title: string;
  description: string;
  emptyTitle?: string;
  emptyDescription?: string;
};

export function ModulePlaceholder({
  title,
  description,
  emptyTitle = "No records yet",
  emptyDescription = "Data for this module will appear here once it is connected to the service layer and seed script.",
}: ModulePlaceholderProps) {
  return (
    <div>
      <PageHeader title={title} description={description} />
      <EmptyState title={emptyTitle} description={emptyDescription} />
    </div>
  );
}
