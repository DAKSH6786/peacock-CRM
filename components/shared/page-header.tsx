type PageHeaderProps = {
  title: string;
  description?: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <header className="mb-8">
      <h1 className="font-[family-name:var(--font-display)] text-4xl font-extrabold tracking-tighter text-black md:text-5xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-3 max-w-2xl font-[family-name:var(--font-body)] text-sm font-medium text-black/70">
          {description}
        </p>
      ) : null}
    </header>
  );
}
