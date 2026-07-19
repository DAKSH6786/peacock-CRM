export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(15,107,76,0.12),transparent_45%),linear-gradient(315deg,rgba(196,163,90,0.16),transparent_40%)]"
      />
      <div className="relative w-full max-w-md">{children}</div>
    </div>
  );
}
