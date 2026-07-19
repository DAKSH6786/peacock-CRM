export default function AppLoading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <div className="h-10 w-56 animate-pulse rounded-[0.75rem] border-2 border-black bg-[#ffe17c]" />
      <div className="h-4 w-96 max-w-full animate-pulse rounded border-2 border-black bg-[#b7c6c2]" />
      <div className="mt-8 h-40 animate-pulse rounded-xl border-2 border-black bg-white shadow-[4px_4px_0_0_#000000]" />
      <span className="sr-only">Loading</span>
    </div>
  );
}
