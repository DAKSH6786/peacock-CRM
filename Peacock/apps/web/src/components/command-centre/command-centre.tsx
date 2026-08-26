"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { IntelligenceFeed } from "@/components/command-centre/intelligence-feed";
import { SituationLayer } from "@/components/command-centre/situation-layer";
import { VisibilityIndex } from "@/components/command-centre/visibility-index";
import {
  DEMO_SNAPSHOT,
  fetchCommandCentrePreview,
  type CommandCentreSnapshot,
} from "@/lib/command-centre";
import { PRODUCT_MODULE_LINKS } from "@/lib/peacock-os";

export function CommandCentre() {
  const [snapshot, setSnapshot] = useState<CommandCentreSnapshot>(DEMO_SNAPSHOT);

  useEffect(() => {
    let active = true;
    void fetchCommandCentrePreview("Acme").then((data) => {
      if (active) setSnapshot(data);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="cc-shell">
      <header className="cc-hero">
        <div className="cc-hero__copy">
          <p className="cc-hero__kicker">Peacock One</p>
          <h1 className="cc-hero__brand" style={{ fontFamily: "var(--font-display)" }}>
            Peacock Command Centre
          </h1>
          <p className="cc-hero__lede">
            Generative visibility command — Adaptive Search, Answer &amp; Generative
            Intelligence OS. Not Semrush + an AI dashboard. One index, the situation
            that matters, and detections you can act on.
          </p>
          <div className="cc-hero__actions">
            <a href="#intelligence-feed" className="cc-btn cc-btn--primary">
              Open intelligence feed
            </a>
            <Link href="/os" className="cc-btn cc-btn--ghost">
              Peacock One OS
            </Link>
            <Link href="/executive" className="cc-btn cc-btn--ghost">
              Executive Brain
            </Link>
            <Link href="/research" className="cc-btn cc-btn--ghost">
              Research Mode
            </Link>
            <Link href="/metrics" className="cc-btn cc-btn--ghost">
              Proprietary Metrics
            </Link>
            <Link href="/ops" className="cc-btn cc-btn--ghost">
              Platform ops
            </Link>
          </div>
        </div>
        <VisibilityIndex
          index={snapshot.visibility_index}
          delta={snapshot.visibility_delta}
          brand={snapshot.client_brand}
          signals={snapshot.signals}
        />
      </header>

      <section className="os-grid" aria-labelledby="cc-modules-title">
        <h2 id="cc-modules-title" style={{ fontFamily: "var(--font-display)" }}>
          Modules
        </h2>
        <p className="os-honesty">
          Open a Peacock One module directly. Each connects to the FastAPI backend where
          available and falls back to a deterministic preview otherwise.
        </p>
        <div className="os-cards">
          {PRODUCT_MODULE_LINKS.map((item) => (
            <Link key={item.href} href={item.href} className="os-card">
              <strong>{item.label}</strong>
              <span>{item.blurb}</span>
            </Link>
          ))}
        </div>
      </section>

      <SituationLayer situations={snapshot.situations} />

      <div id="intelligence-feed">
        <IntelligenceFeed items={snapshot.feed_items} />
      </div>
    </div>
  );
}
