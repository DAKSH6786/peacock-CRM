import { evaluateAeo } from "@/modules/aeo/analyze";
import {
  ROLE_PROMPTS,
  getConnectorRegistry,
  type ConnectorRegistry,
  type ConnectorResponse,
} from "@/modules/connectors";
import { analyzeSite } from "@/modules/crawl/analyze";
import { evaluateGeo } from "@/modules/geo/analyze";
import { buildKnowledgeGraph } from "@/modules/knowledge/graph";
import { evaluateTechnicalSeo } from "@/modules/seo/technical";
import { buildNinetyDayPlan } from "@/modules/strategy/ninety-day";
import {
  detectBrandMention,
  scoreVisibility,
} from "@/modules/visibility/score";

import { rankRecommendations, scoreRecommendation } from "./scoring";
import type {
  DecideArtifacts,
  DecidedRecommendation,
  ExecuteArtifacts,
  LearnArtifacts,
  MeasureArtifacts,
  ObserveArtifacts,
  PipelineProperty,
  PipelineRunResult,
  RecommendationWeights,
  StageResult,
  ThinkArtifacts,
  VerifyArtifacts,
} from "./types";

export type RunPipelineOptions = {
  registry?: ConnectorRegistry;
  weights?: RecommendationWeights;
  /** Optional HTML fixtures for deterministic OBSERVE (tests / offline) */
  pageHtml?: Array<{ url: string; html: string; statusCode?: number }>;
  probeQuestion?: string;
  /** Minimum consensus to allow EXECUTE */
  minConsensus?: number;
};

/**
 * Full cognitive loop — OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN.
 * Stages request connector *roles* with distinct templates; never identical fan-out.
 */
export async function runIntelligencePipeline(
  property: PipelineProperty,
  options: RunPipelineOptions = {},
): Promise<PipelineRunResult> {
  const registry = options.registry ?? getConnectorRegistry();
  const weights = options.weights ?? {};
  const minConsensus = options.minConsensus ?? 0.55;
  const stages: PipelineRunResult["stages"] = {};

  try {
    const observe = await stageObserve(property, registry, options.pageHtml);
    stages.OBSERVE = observe;
    if (observe.status !== "SUCCEEDED") {
      return fail(property, stages, "OBSERVE failed");
    }

    const think = await stageThink(property, observe.output, registry);
    stages.THINK = think;
    if (think.status !== "SUCCEEDED") {
      return fail(property, stages, "THINK failed");
    }

    const verify = await stageVerify(
      property,
      observe.output,
      think.output,
      registry,
      minConsensus,
    );
    stages.VERIFY = verify;

    if (verify.output.blocked || verify.status === "BLOCKED") {
      return {
        property,
        status: "BLOCKED_ON_VERIFY",
        stages,
        observe: observe.output,
        think: think.output,
        verify: verify.output,
        summary: `VERIFY blocked execution: ${verify.output.reasons.join("; ")}`,
        confidence: verify.confidence,
      };
    }

    const decide = stageDecide(
      property,
      observe.output,
      think.output,
      verify.output,
      weights,
    );
    stages.DECIDE = decide;

    const execute = await stageExecute(
      property,
      decide.output,
      observe.output,
      registry,
    );
    stages.EXECUTE = execute;

    const measure = await stageMeasure(
      property,
      registry,
      options.probeQuestion,
    );
    stages.MEASURE = measure;

    const learn = stageLearn(decide.output, measure.output);
    stages.LEARN = learn;

    const confidence = average([
      observe.confidence,
      think.confidence,
      verify.confidence,
      decide.confidence,
      execute.confidence,
      measure.confidence,
      learn.confidence,
    ]);

    return {
      property,
      status: "COMPLETED",
      stages,
      observe: observe.output,
      think: think.output,
      verify: verify.output,
      decide: decide.output,
      execute: execute.output,
      measure: measure.output,
      learn: learn.output,
      summary: `Completed cognitive loop for ${property.brand}: ${decide.output.recommendations.length} recommendations, visibility mention rate ${(measure.output.scorecard.mentionRate * 100).toFixed(0)}%.`,
      confidence,
    };
  } catch (error) {
    return fail(
      property,
      stages,
      error instanceof Error ? error.message : "Unknown pipeline error",
    );
  }
}

async function stageObserve(
  property: PipelineProperty,
  registry: ConnectorRegistry,
  pageHtml?: RunPipelineOptions["pageHtml"],
): Promise<StageResult<ObserveArtifacts>> {
  const traces: ConnectorResponse[] = [];
  const pagesInput = pageHtml ?? [
    {
      url: property.rootUrl,
      html: demoHomeHtml(property),
    },
    {
      url: `${property.rootUrl.replace(/\/$/, "")}/about`,
      html: demoAboutHtml(property),
    },
  ];

  const { pages, technicalSummary } = analyzeSite(pagesInput);
  const technicalFindings = evaluateTechnicalSeo(pages);
  const aeo = evaluateAeo(pages);
  const geo = evaluateGeo(pages, property.brand);

  const research = await registry.runRole({
    role: "WEB_RESEARCH",
    templateId: ROLE_PROMPTS.WEB_RESEARCH.templateId,
    evidence: {
      brand: property.brand,
      domain: property.domain,
      technicalSummary,
    },
    variables: {
      brand: property.brand,
      domain: property.domain,
      topics: (property.keywords ?? ["category leadership"]).join(", "),
    },
  });
  traces.push(research);

  const citations = await registry.runRole({
    role: "CITATION_HUNT",
    templateId: ROLE_PROMPTS.CITATION_HUNT.templateId,
    evidence: { brand: property.brand, domain: property.domain },
    variables: {
      brand: property.brand,
      topics: (property.keywords ?? ["buyers guide"]).join(", "),
    },
  });
  traces.push(citations);

  registry.assertNotIdenticalFanout(
    traces.map((t) => ({ role: t.role, templateId: t.templateId })),
  );

  return {
    stage: "OBSERVE",
    status: "SUCCEEDED",
    confidence: 0.85,
    traces,
    output: {
      pages,
      technicalSummary,
      technicalFindings,
      aeo,
      geo,
      research,
      citations,
    },
  };
}

async function stageThink(
  property: PipelineProperty,
  observe: ObserveArtifacts,
  registry: ConnectorRegistry,
): Promise<StageResult<ThinkArtifacts>> {
  const evidenceSummary = JSON.stringify({
    technical: observe.technicalFindings.map((f) => f.code),
    aeo: observe.aeo.findings.map((f) => f.code),
    geo: observe.geo.findings.map((f) => f.code),
  });

  const structural = await registry.runRole({
    role: "STRUCTURAL_CRITIQUE",
    templateId: ROLE_PROMPTS.STRUCTURAL_CRITIQUE.templateId,
    evidence: {
      brand: property.brand,
      domain: property.domain,
      pages: observe.pages,
      technicalFindings: observe.technicalFindings,
    },
    variables: {
      domain: property.domain,
      evidenceSummary,
    },
  });

  const contentQuality = await registry.runRole({
    role: "CONTENT_QUALITY",
    templateId: ROLE_PROMPTS.CONTENT_QUALITY.templateId,
    evidence: {
      brand: property.brand,
      domain: property.domain,
      pages: observe.pages,
    },
    variables: {
      domain: property.domain,
      competitorThemes: (property.competitors ?? [])
        .map((c) => c.name)
        .join(", "),
    },
  });

  const entities = await registry.runRole({
    role: "ENTITY_EXTRACTION",
    templateId: ROLE_PROMPTS.ENTITY_EXTRACTION.templateId,
    evidence: {
      brand: property.brand,
      domain: property.domain,
      pages: observe.pages,
    },
    variables: { domain: property.domain },
  });

  const extracted =
    (entities.structured?.entities as Array<{ name: string; type: string }>) ??
    [];
  const graph = buildKnowledgeGraph({
    brand: property.brand,
    domain: property.domain,
    extracted,
  });

  const knowledgeLinks = await registry.runRole({
    role: "KNOWLEDGE_LINK",
    templateId: ROLE_PROMPTS.KNOWLEDGE_LINK.templateId,
    evidence: { brand: property.brand, graph },
    variables: {
      brand: property.brand,
      entities: graph.nodes.map((n) => n.name).join(", "),
    },
  });

  const specialistSummaries = [
    structural.content,
    contentQuality.content,
    entities.content,
    knowledgeLinks.content,
    observe.research?.content,
  ]
    .filter(Boolean)
    .join("\n---\n");

  const synthesis = await registry.runRole({
    role: "SYNTHESIS",
    templateId: ROLE_PROMPTS.SYNTHESIS.templateId,
    evidence: {
      brand: property.brand,
      specialists: {
        structural: structural.promptHash,
        contentQuality: contentQuality.promptHash,
        entities: entities.promptHash,
      },
    },
    variables: {
      brand: property.brand,
      specialistSummaries,
    },
  });

  const secondOpinion = await registry.runRole({
    role: "SECOND_OPINION",
    templateId: ROLE_PROMPTS.SECOND_OPINION.templateId,
    evidence: { brand: property.brand, synthesisHash: synthesis.promptHash },
    variables: {
      brand: property.brand,
      synthesis: synthesis.content,
    },
  });

  const costSweep = await registry.runRole({
    role: "COST_SWEEP",
    templateId: ROLE_PROMPTS.COST_SWEEP.templateId,
    evidence: { technicalFindings: observe.technicalFindings },
    variables: {
      technicalFindings: observe.technicalFindings
        .map((f) => f.code)
        .join(", "),
    },
  });

  const traces = [
    structural,
    contentQuality,
    entities,
    knowledgeLinks,
    synthesis,
    secondOpinion,
    costSweep,
  ];
  registry.assertNotIdenticalFanout(
    traces.map((t) => ({ role: t.role, templateId: t.templateId })),
  );

  // Guard: THINK templates must not reuse the visibility probe template
  if (traces.some((t) => t.templateId === "measure.visibility_probe")) {
    throw new Error("THINK stage must not use visibility probe templates");
  }

  return {
    stage: "THINK",
    status: "SUCCEEDED",
    confidence: 0.78,
    traces,
    output: {
      structural,
      contentQuality,
      entities,
      knowledgeLinks,
      synthesis,
      secondOpinion,
      costSweep,
      graph,
    },
  };
}

async function stageVerify(
  property: PipelineProperty,
  observe: ObserveArtifacts,
  think: ThinkArtifacts,
  registry: ConnectorRegistry,
  minConsensus: number,
): Promise<StageResult<VerifyArtifacts>> {
  const claims = [
    ...observe.technicalFindings.map((f) => f.code),
    ...observe.aeo.findings.map((f) => f.code),
    ...observe.geo.findings.map((f) => f.code),
    "synthesis_pillars",
  ];

  const deterministicPass =
    observe.pages.length > 0 && observe.technicalFindings !== undefined;

  const adversarial = await registry.runRole({
    role: "VERIFY_ADVERSARIAL",
    templateId: ROLE_PROMPTS.VERIFY_ADVERSARIAL.templateId,
    evidence: {
      brand: property.brand,
      pages: observe.pages.map((p) => p.url),
      thinkHashes: {
        synthesis: think.synthesis?.promptHash,
        structural: think.structural?.promptHash,
      },
    },
    variables: {
      claims: claims.join(", "),
      evidenceKeys: ["pages", "technicalFindings", "aeo", "geo"].join(", "),
    },
  });

  const consensus = await registry.runRole({
    role: "VERIFY_CONSENSUS",
    templateId: ROLE_PROMPTS.VERIFY_CONSENSUS.templateId,
    evidence: { brand: property.brand },
    variables: {
      specialistSummaries: [
        think.synthesis?.content,
        think.secondOpinion?.content,
        think.structural?.content,
      ]
        .filter(Boolean)
        .join("\n"),
    },
  });

  const acceptedClaims =
    (adversarial.structured?.accepted as string[]) ?? claims.slice(0, 2);
  const rejectedClaims = (adversarial.structured?.rejected as string[]) ?? [];
  const consensusScore =
    typeof consensus.structured?.consensus === "number"
      ? (consensus.structured.consensus as number)
      : 0.5;

  const reasons: string[] = [];
  if (!deterministicPass) reasons.push("deterministic observers failed");
  if (consensusScore < minConsensus) {
    reasons.push(`consensus ${consensusScore} below threshold ${minConsensus}`);
  }

  const blocked = reasons.length > 0;

  return {
    stage: "VERIFY",
    status: blocked ? "BLOCKED" : "SUCCEEDED",
    confidence: consensusScore,
    traces: [adversarial, consensus],
    output: {
      deterministicPass,
      adversarial,
      consensus,
      acceptedClaims,
      rejectedClaims,
      consensusScore,
      blocked,
      reasons,
    },
  };
}

function stageDecide(
  property: PipelineProperty,
  observe: ObserveArtifacts,
  think: ThinkArtifacts,
  verify: VerifyArtifacts,
  weights: RecommendationWeights,
): StageResult<DecideArtifacts> {
  const raw: Array<
    Omit<DecidedRecommendation, "confidence"> & { confidence?: number }
  > = [];

  for (const finding of observe.technicalFindings.slice(0, 5)) {
    raw.push({
      kind: "TECHNICAL_SEO",
      title: `Remediate ${finding.code}`,
      summary: finding.message,
      rationale: `Observed on ${finding.url ?? property.domain}`,
      impactScore: finding.severity === "high" ? 0.85 : 0.55,
      effortScore: finding.severity === "high" ? 0.35 : 0.25,
      confidence: 0.9,
      evidenceRefs: [finding.id],
      features: { severity_high: finding.severity === "high" ? 1 : 0 },
    });
  }

  for (const finding of observe.aeo.findings) {
    raw.push({
      kind: "AEO",
      title: `AEO: ${finding.code}`,
      summary: finding.message,
      rationale: "Answer-engine extractability gap",
      impactScore: 0.7,
      effortScore: 0.4,
      confidence: verify.consensusScore,
      evidenceRefs: [finding.id],
      features: { aeo_gap: 1 },
    });
  }

  for (const finding of observe.geo.findings) {
    raw.push({
      kind: "GEO",
      title: `GEO: ${finding.code}`,
      summary: finding.message,
      rationale: "Generative engine grounding gap",
      impactScore: 0.75,
      effortScore: 0.35,
      confidence: verify.consensusScore,
      evidenceRefs: [finding.id],
      features: { geo_gap: 1 },
    });
  }

  raw.push({
    kind: "WRITER",
    title: "Publish answer-led content cluster",
    summary: "Writer pack for priority intents grounded in synthesis",
    rationale: think.synthesis?.content.slice(0, 180) ?? "Synthesis",
    impactScore: 0.8,
    effortScore: 0.55,
    confidence: verify.consensusScore,
    evidenceRefs: ["synthesis"],
    features: { content_cluster: 1 },
  });

  raw.push({
    kind: "STRATEGY",
    title: "Approve 90-day visibility strategy",
    summary: "Sequenced technical → entity → answer → authority plan",
    rationale: "Decided from verified priorities",
    impactScore: 0.9,
    effortScore: 0.2,
    confidence: verify.consensusScore,
    evidenceRefs: ["verify"],
    features: { strategy: 1 },
  });

  const recommendations = rankRecommendations(
    raw.map((r) => scoreRecommendation(r, weights)),
  );
  const priorities = recommendations.slice(0, 5).map((r) => r.title);

  return {
    stage: "DECIDE",
    status: "SUCCEEDED",
    confidence: verify.consensusScore,
    traces: [],
    output: { recommendations, priorities },
  };
}

async function stageExecute(
  property: PipelineProperty,
  decide: DecideArtifacts,
  observe: ObserveArtifacts,
  registry: ConnectorRegistry,
): Promise<StageResult<ExecuteArtifacts>> {
  const writerRecs = decide.recommendations
    .filter(
      (r) => r.kind === "WRITER" || r.kind === "CONTENT" || r.kind === "AEO",
    )
    .slice(0, 2);
  const writerBriefs: ConnectorResponse[] = [];
  for (const rec of writerRecs) {
    writerBriefs.push(
      await registry.runRole({
        role: "WRITER_BRIEF",
        templateId: ROLE_PROMPTS.WRITER_BRIEF.templateId,
        evidence: { recommendation: rec, brand: property.brand },
        variables: {
          recommendationTitle: rec.title,
          recommendationSummary: rec.summary,
        },
      }),
    );
  }

  const strategyFrame = await registry.runRole({
    role: "STRATEGY_FRAME",
    templateId: ROLE_PROMPTS.STRATEGY_FRAME.templateId,
    evidence: { priorities: decide.priorities, brand: property.brand },
    variables: {
      brand: property.brand,
      priorities: decide.priorities.join("; "),
    },
  });

  const strategy = buildNinetyDayPlan({
    brand: property.brand,
    priorities: decide.priorities,
    technicalCodes: observe.technicalFindings.map((f) => f.code),
    aeoCodes: observe.aeo.findings.map((f) => f.code),
    geoCodes: observe.geo.findings.map((f) => f.code),
  });

  return {
    stage: "EXECUTE",
    status: "SUCCEEDED",
    confidence: 0.8,
    traces: [...writerBriefs, strategyFrame],
    output: { writerBriefs, strategy, strategyFrame },
  };
}

async function stageMeasure(
  property: PipelineProperty,
  registry: ConnectorRegistry,
  probeQuestion?: string,
): Promise<StageResult<MeasureArtifacts>> {
  const question =
    probeQuestion ??
    `What are the best platforms for enterprise generative search visibility like ${property.brand}?`;

  const surfaces = [
    "CHATGPT",
    "GEMINI",
    "CLAUDE",
    "PERPLEXITY",
    "DEEPSEEK",
  ] as const;

  const probes = await registry.runVisibilityProbes({
    brand: property.brand,
    domain: property.domain,
    probeQuestion: question,
    surfaces: [...surfaces],
  });

  for (const probe of probes) {
    if (probe.templateId !== "measure.visibility_probe") {
      throw new Error("MEASURE must use visibility probe templates only");
    }
  }

  const labeled = probes.map((p, idx) => {
    const surface = surfaces[idx] ?? p.provider;
    const detected = detectBrandMention(
      p.content,
      property.brand,
      property.domain,
    );
    return {
      surface,
      mentionedBrand:
        Boolean(p.structured?.mentionedBrand) || detected.mentionedBrand,
      citedUrl: Boolean(p.structured?.citedUrl) || detected.citedUrl,
      excerpt: p.content.slice(0, 240),
    };
  });

  return {
    stage: "MEASURE",
    status: "SUCCEEDED",
    confidence: 0.75,
    traces: probes,
    output: {
      probes,
      scorecard: scoreVisibility(labeled),
    },
  };
}

function stageLearn(
  decide: DecideArtifacts,
  measure: MeasureArtifacts,
): StageResult<LearnArtifacts> {
  const mention = measure.scorecard.mentionRate;
  const weightUpdates = decide.recommendations.slice(0, 5).map((r) => ({
    kind: r.kind,
    featureKey: Object.keys(r.features)[0] ?? "default",
    delta: mention >= 0.5 ? 0.05 : -0.03,
  }));

  return {
    stage: "LEARN",
    status: "SUCCEEDED",
    confidence: 0.7,
    traces: [],
    output: {
      weightUpdates,
      signals: [
        { key: "mention_rate", value: mention },
        { key: "citation_rate", value: measure.scorecard.citationRate },
        {
          key: "recommendation_count",
          value: decide.recommendations.length,
        },
      ],
    },
  };
}

function fail(
  property: PipelineProperty,
  stages: PipelineRunResult["stages"],
  message: string,
): PipelineRunResult {
  return {
    property,
    status: "FAILED",
    stages,
    summary: message,
    confidence: 0,
  };
}

function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function demoHomeHtml(property: PipelineProperty): string {
  return `<!doctype html><html><head>
<title>${property.brand} — Home</title>
<meta name="description" content="${property.brand} generative visibility platform" />
<link rel="canonical" href="${property.rootUrl}" />
<script type="application/ld+json">{"@type":"WebSite","name":"${property.brand}"}</script>
</head><body>
<h1>${property.brand}</h1>
<h2>What is generative visibility?</h2>
<p>${"Insight ".repeat(100)}</p>
</body></html>`;
}

function demoAboutHtml(property: PipelineProperty): string {
  return `<!doctype html><html><head>
<title>About ${property.brand}</title>
</head><body>
<h1>About</h1>
<p>${"About ".repeat(40)}</p>
</body></html>`;
}
