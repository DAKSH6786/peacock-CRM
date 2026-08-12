import { ArchitecturePanel } from "@/components/architecture-panel";
import { HealthCard } from "@/components/health-card";
import { LoginForm } from "@/components/login-form";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-12">
      <header className="space-y-4">
        <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
          Peacock One
        </p>
        <h1
          className="max-w-3xl text-4xl font-bold tracking-tight md:text-6xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Generative visibility intelligence architecture
        </h1>
        <p className="max-w-2xl text-lg text-[var(--muted)]">
          OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN. This
          stage ships the monorepo, auth boundaries, job runtime, and LLM
          adapter ports — not business features yet.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <HealthCard />
        <LoginForm />
      </div>

      <ArchitecturePanel />
    </main>
  );
}
