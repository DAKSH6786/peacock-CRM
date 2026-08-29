"use client";

import type { SituationItem } from "@/lib/command-centre";

type Props = {
  situations: SituationItem[];
};

export function SituationLayer({ situations }: Props) {
  return (
    <section className="cc-situation" aria-labelledby="cc-situation-title">
      <div className="cc-section-head">
        <h2 id="cc-situation-title" style={{ fontFamily: "var(--font-display)" }}>
          Situation
        </h2>
        <p>Second layer — what demands attention now.</p>
      </div>
      <ol className="cc-situation__list">
        {situations.map((item) => (
          <li key={item.kind} data-severity={item.severity}>
            <span className="cc-situation__kind">{item.label}</span>
            <span className="cc-situation__title" style={{ fontFamily: "var(--font-display)" }}>
              {item.title}
            </span>
            <span className="cc-situation__detail">{item.detail}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
