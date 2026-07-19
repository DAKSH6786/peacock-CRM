import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed border-black bg-white px-6 py-16 text-center shadow-[4px_4px_0_0_#000000]"
      role="status"
    >
      <span className="flex h-16 w-16 items-center justify-center rounded-xl border-2 border-black bg-[#b7c6c2] shadow-[4px_4px_0_0_#000000] transition-colors hover:bg-[#ffe17c]">
        <Inbox className="h-7 w-7 text-black" aria-hidden />
      </span>
      <div>
        <h2 className="font-[family-name:var(--font-display)] text-2xl font-extrabold tracking-tighter">
          {title}
        </h2>
        <p className="mt-2 max-w-md font-[family-name:var(--font-body)] text-sm font-medium text-black/70">
          {description}
        </p>
      </div>
    </div>
  );
}
