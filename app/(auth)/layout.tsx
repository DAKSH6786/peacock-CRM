export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-dot-pattern relative min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-10 lg:px-8">
        {children}
      </div>
    </div>
  );
}
