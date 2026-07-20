export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(900px_500px_at_10%_-10%,rgba(45,212,191,0.16),transparent_55%),radial-gradient(700px_420px_at_90%_0%,rgba(139,92,246,0.12),transparent_50%),var(--background)]"
      />
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-10 lg:px-8">
        {children}
      </div>
    </div>
  );
}
