import { cn, initials } from "@/lib/utils";

type AvatarGroupProps = {
  people: Array<{ id: string; name: string }>;
  max?: number;
};

export function AvatarGroup({ people, max = 4 }: AvatarGroupProps) {
  const visible = people.slice(0, max);
  const remaining = Math.max(people.length - max, 0);

  return (
    <ul className="flex -space-x-2" aria-label="People">
      {visible.map((person) => (
        <li
          key={person.id}
          title={person.name}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full border-2 border-[var(--surface)] bg-[var(--primary)] text-[10px] font-bold text-[var(--primary-foreground)]",
          )}
        >
          <span className="sr-only">{person.name}</span>
          <span aria-hidden>{initials(person.name)}</span>
        </li>
      ))}
      {remaining > 0 ? (
        <li className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-[var(--surface)] bg-[var(--surface-muted)] text-[10px] font-bold text-[var(--muted)]">
          +{remaining}
        </li>
      ) : null}
    </ul>
  );
}
