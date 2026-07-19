export function BrowserMockup() {
  return (
    <div
      className="overflow-hidden rounded-2xl border-2 border-black bg-white shadow-[12px_12px_0_0_#000000]"
      aria-hidden
    >
      <div className="flex items-center gap-2 border-b-2 border-black bg-black px-4 py-3">
        <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
        <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
        <span className="h-3 w-3 rounded-full bg-[#28c840]" />
        <span className="ml-3 h-5 flex-1 rounded border border-[#272727] bg-[#272727]" />
      </div>
      <div className="grid gap-3 p-4 sm:grid-cols-3">
        <div className="rounded-xl border-2 border-black bg-[#b7c6c2] p-4 sm:col-span-2">
          <p className="font-[family-name:var(--font-display)] text-sm font-extrabold tracking-tighter">
            Pipeline revenue
          </p>
          <div className="mt-4 flex h-24 items-end gap-2">
            {[40, 65, 45, 80, 55, 90, 70].map((h, i) => (
              <div
                key={i}
                className="flex-1 border-2 border-black bg-[#ffe17c]"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>
        <div className="rounded-xl border-2 border-black bg-[#171e19] p-4 text-white">
          <p className="font-[family-name:var(--font-display)] text-sm font-extrabold tracking-tighter">
            Active deals
          </p>
          <p className="mt-6 font-[family-name:var(--font-display)] text-4xl font-extrabold tracking-tighter text-[#ffe17c]">
            24
          </p>
          <p className="mt-2 text-xs font-medium text-[#b7c6c2]">
            This quarter
          </p>
        </div>
        <div className="rounded-xl border-2 border-black bg-white p-4 sm:col-span-3">
          <div className="flex items-center justify-between gap-3">
            <p className="font-[family-name:var(--font-display)] text-sm font-extrabold tracking-tighter">
              Team workload
            </p>
            <span className="rounded-full border-2 border-black bg-[#ffe17c] px-2 py-0.5 text-[10px] font-bold">
              LIVE
            </span>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full border-2 border-black bg-[#f4f4f5]">
            <div className="h-full w-2/3 bg-[#b7c6c2]" />
          </div>
        </div>
      </div>
    </div>
  );
}
