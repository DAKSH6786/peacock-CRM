export type CrawlPageInput = {
  url: string;
  html?: string;
  statusCode?: number;
};

export type CrawlPageArtifact = {
  url: string;
  statusCode: number;
  title: string | null;
  metaDescription: string | null;
  canonical: string | null;
  wordCount: number;
  headings: string[];
  schemaTypes: string[];
  technicalFlags: string[];
  contentHash: string;
};

/**
 * Deterministic OBSERVE helper — parses HTML signals without LLMs.
 */
export function analyzePage(input: CrawlPageInput): CrawlPageArtifact {
  const html = input.html ?? minimalShell(input.url);
  const title = matchTag(html, "title");
  const metaDescription =
    html.match(
      /<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["']/i,
    )?.[1] ??
    html.match(
      /<meta[^>]+content=["']([^"']*)["'][^>]+name=["']description["']/i,
    )?.[1] ??
    null;
  const canonical =
    html.match(
      /<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']/i,
    )?.[1] ?? null;
  const headings = [...html.matchAll(/<h([1-3])[^>]*>(.*?)<\/h\1>/gis)].map(
    (m) => stripTags(m[2] ?? ""),
  );
  const schemaTypes = [...html.matchAll(/"@type"\s*:\s*"([^"]+)"/g)].map(
    (m) => m[1]!,
  );
  const text = stripTags(html);
  const technicalFlags: string[] = [];
  if (!title) technicalFlags.push("missing_title");
  if (!metaDescription) technicalFlags.push("missing_meta_description");
  if (!canonical) technicalFlags.push("missing_canonical");
  if (!schemaTypes.length) technicalFlags.push("missing_jsonld");
  if (text.split(/\s+/).filter(Boolean).length < 120) {
    technicalFlags.push("thin_content");
  }

  return {
    url: input.url,
    statusCode: input.statusCode ?? 200,
    title,
    metaDescription,
    canonical,
    wordCount: text.split(/\s+/).filter(Boolean).length,
    headings,
    schemaTypes,
    technicalFlags,
    contentHash: cheapHash(text),
  };
}

export function analyzeSite(pages: CrawlPageInput[]): {
  pages: CrawlPageArtifact[];
  technicalSummary: Record<string, number>;
} {
  const analyzed = pages.map(analyzePage);
  const technicalSummary: Record<string, number> = {};
  for (const page of analyzed) {
    for (const flag of page.technicalFlags) {
      technicalSummary[flag] = (technicalSummary[flag] ?? 0) + 1;
    }
  }
  return { pages: analyzed, technicalSummary };
}

function matchTag(html: string, tag: string): string | null {
  const m = html.match(new RegExp(`<${tag}[^>]*>(.*?)</${tag}>`, "is"));
  return m ? stripTags(m[1] ?? "") : null;
}

function stripTags(value: string): string {
  return value
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function cheapHash(value: string): string {
  let h = 0;
  for (let i = 0; i < value.length; i += 1) {
    h = (Math.imul(31, h) + value.charCodeAt(i)) | 0;
  }
  return `h${Math.abs(h)}`;
}

function minimalShell(url: string): string {
  return `<!doctype html><html><head><title>${url}</title></head><body><h1>Page</h1><p>${"word ".repeat(80)}</p></body></html>`;
}
