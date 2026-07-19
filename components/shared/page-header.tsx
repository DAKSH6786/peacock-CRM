type PageHeaderProps = {
  title: string;
  description?: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <header className="mb-8">
      <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-[var(--foreground)]">
        {title}
      </h1>
      {description ? (
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          {description}
        </p>
      ) : null}
    </header>
  );
}
