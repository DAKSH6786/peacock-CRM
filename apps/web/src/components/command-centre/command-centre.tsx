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
            Generative visibility command — not another SEO dashboard. One index,
            the situation that matters, and detections you can act on.
          </p>
          <div className="cc-hero__actions">
            <a href="#intelligence-feed" className="cc-btn cc-btn--primary">
              Open intelligence feed
            </a>
            <Link href="/executive" className="cc-btn cc-btn--ghost">
              Executive Brain
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

      <SituationLayer situations={snapshot.situations} />

      <div id="intelligence-feed">
        <IntelligenceFeed items={snapshot.feed_items} />
      </div>
    </div>
  );
}
