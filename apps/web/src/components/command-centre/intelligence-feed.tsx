"use client";

import type { FeedItem } from "@/lib/command-centre";

type Props = {
  items: FeedItem[];
};

export function IntelligenceFeed({ items }: Props) {
  return (
    <section className="cc-feed" aria-labelledby="cc-feed-title">
      <div className="cc-section-head">
        <h2 id="cc-feed-title" style={{ fontFamily: "var(--font-display)" }}>
          Intelligence feed
        </h2>
        <p>Live detections from the Peacock intelligence graph.</p>
      </div>
      <div className="cc-feed__stream">
        {items.map((item, index) => (
          <article
            key={`${item.feed_index}-${item.headline}`}
            className="cc-feed__item"
            style={{ animationDelay: `${0.08 * index}s` }}
          >
            <p className="cc-feed__label">{item.detection_label}</p>
            <h3 style={{ fontFamily: "var(--font-display)" }}>{item.headline}</h3>
            <p className="cc-feed__body">{item.body}</p>
            <dl className="cc-feed__meta">
              <div>
                <dt>Primary driver</dt>
                <dd>{item.primary_driver}</dd>
              </div>
              <div>
                <dt>Potential response</dt>
                <dd>{item.potential_response}</dd>
              </div>
              <div>
                <dt>Confidence</dt>
                <dd>{item.confidence_pct}%</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
