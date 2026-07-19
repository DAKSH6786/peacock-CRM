import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg rounded-xl border-2 border-black bg-white px-6 py-12 text-center shadow-[8px_8px_0_0_#000000]">
      <h1 className="font-[family-name:var(--font-display)] text-3xl font-extrabold tracking-tighter">
        Page not found
      </h1>
      <p className="mt-3 font-[family-name:var(--font-body)] text-sm font-medium text-black/70">
        The page you requested does not exist in Peacock One.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex h-11 items-center justify-center rounded-[0.75rem] border-2 border-black bg-black px-5 text-sm font-bold text-white shadow-[8px_8px_0_0_#000000] transition-all duration-200 hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-[4px_4px_0_0_#000000]"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
