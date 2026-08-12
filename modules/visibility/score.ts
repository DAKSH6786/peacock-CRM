export type VisibilityProbeResult = {
  surface: string;
  mentionedBrand: boolean;
  citedUrl: boolean;
  excerpt: string;
};

export type VisibilityScorecard = {
  mentionRate: number;
  citationRate: number;
  bySurface: Array<{
    surface: string;
    mentionedBrand: boolean;
    citedUrl: boolean;
  }>;
};

export function scoreVisibility(
  probes: VisibilityProbeResult[],
): VisibilityScorecard {
  if (!probes.length) {
    return { mentionRate: 0, citationRate: 0, bySurface: [] };
  }
  const mentions = probes.filter((p) => p.mentionedBrand).length;
  const citations = probes.filter((p) => p.citedUrl).length;
  return {
    mentionRate: mentions / probes.length,
    citationRate: citations / probes.length,
    bySurface: probes.map((p) => ({
      surface: p.surface,
      mentionedBrand: p.mentionedBrand,
      citedUrl: p.citedUrl,
    })),
  };
}

export function detectBrandMention(
  text: string,
  brand: string,
  domain: string,
): { mentionedBrand: boolean; citedUrl: boolean } {
  const lower = text.toLowerCase();
  return {
    mentionedBrand: lower.includes(brand.toLowerCase()),
    citedUrl: lower.includes(domain.toLowerCase()),
  };
}
