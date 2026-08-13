"use client";

import type { VisibilitySignal } from "@/lib/command-centre";

type Props = {
  index: number;
  delta: number;
  brand: string;
  signals: VisibilitySignal[];
};

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

export function VisibilityIndex({ index, delta, brand, signals }: Props) {
  const size = 420;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 148;
  const n = Math.max(signals.length, 1);
  const points = signals
    .map((s, i) => {
      const angle = (360 / n) * i;
      const r = (Math.max(0, Math.min(100, s.score)) / 100) * maxR;
      return polar(cx, cy, r, angle);
    })
    .map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const deltaLabel = `${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`;

  return (
    <div className="cc-index">
      <div className="cc-index__stage">
        <div className="cc-index__orb" aria-hidden>
          <svg viewBox={`0 0 ${size} ${size}`} className="cc-index__svg">
            <defs>
              <radialGradient id="ccOrbGlow" cx="50%" cy="45%" r="65%">
                <stop offset="0%" stopColor="rgba(45, 212, 191, 0.28)" />
                <stop offset="55%" stopColor="rgba(14, 116, 144, 0.12)" />
                <stop offset="100%" stopColor="rgba(7, 17, 31, 0)" />
              </radialGradient>
            </defs>
            <circle cx={cx} cy={cy} r={maxR + 36} fill="url(#ccOrbGlow)" />
            {[0.35, 0.65, 1].map((t) => (
              <circle
                key={t}
                cx={cx}
                cy={cy}
                r={maxR * t}
                fill="none"
                stroke="rgba(232, 238, 247, 0.08)"
                strokeWidth="1"
              />
            ))}
            {signals.map((s, i) => {
              const angle = (360 / n) * i;
              const tip = polar(cx, cy, maxR + 8, angle);
              return (
                <line
                  key={s.dimension}
                  x1={cx}
                  y1={cy}
                  x2={tip.x}
                  y2={tip.y}
                  stroke="rgba(232, 238, 247, 0.08)"
                  strokeWidth="1"
                />
              );
            })}
            <polygon
              points={points}
              fill="rgba(45, 212, 191, 0.18)"
              stroke="rgba(45, 212, 191, 0.85)"
              strokeWidth="2"
              className="cc-index__poly"
            />
            {signals.map((s, i) => {
              const angle = (360 / n) * i;
              const r = (Math.max(0, Math.min(100, s.score)) / 100) * maxR;
              const p = polar(cx, cy, r, angle);
              return <circle key={s.dimension} cx={p.x} cy={p.y} r="3.5" fill="#5eead4" />;
            })}
          </svg>
        </div>

        <div className="cc-index__readout">
          <p className="cc-index__brand">{brand}</p>
          <p className="cc-index__label">Peacock Visibility Index</p>
          <p className="cc-index__value" style={{ fontFamily: "var(--font-display)" }}>
            {index.toFixed(0)}
          </p>
          <p className={`cc-index__delta ${delta < 0 ? "is-down" : "is-up"}`}>
            {deltaLabel} this window
          </p>
        </div>
      </div>

      <ul className="cc-index__legend">
        {signals.map((s) => (
          <li key={s.dimension}>
            <span>{s.label}</span>
            <strong>
              {s.score.toFixed(0)}
              <em className={s.delta < 0 ? "is-down" : "is-up"}>
                {s.delta >= 0 ? "+" : ""}
                {s.delta.toFixed(1)}
              </em>
            </strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
