import "server-only";

import type { Prisma } from "@prisma/client";

import { prisma } from "@/database";

import { runIntelligencePipeline } from "./pipeline";
import type { PipelineProperty, PipelineRunResult } from "./types";

export type EnsurePropertyInput = {
  organizationId: string;
  name: string;
  brand?: string;
  primaryDomain: string;
  rootUrl: string;
  industry?: string;
};

export async function ensureVisibilityProperty(input: EnsurePropertyInput) {
  const existing = await prisma.visibilityProperty.findFirst({
    where: {
      organizationId: input.organizationId,
      primaryDomain: input.primaryDomain,
      deletedAt: null,
    },
  });
  if (existing) return existing;

  return prisma.visibilityProperty.create({
    data: {
      organizationId: input.organizationId,
      name: input.name,
      primaryDomain: input.primaryDomain,
      rootUrl: input.rootUrl,
      industry: input.industry,
      metadata: { brand: input.brand ?? input.name },
    },
  });
}

export async function listVisibilityProperties(organizationId: string) {
  return prisma.visibilityProperty.findMany({
    where: { organizationId, deletedAt: null },
    orderBy: { createdAt: "desc" },
    include: {
      _count: {
        select: { intelligenceRuns: true, recommendations: true },
      },
    },
  });
}

export async function listRecentRuns(organizationId: string, take = 10) {
  return prisma.intelligenceRun.findMany({
    where: { organizationId },
    orderBy: { createdAt: "desc" },
    take,
    include: {
      property: { select: { id: true, name: true, primaryDomain: true } },
      stages: true,
    },
  });
}

export async function getIntelligenceOverview(organizationId: string) {
  const [properties, runs, recommendations, weights] = await Promise.all([
    listVisibilityProperties(organizationId),
    listRecentRuns(organizationId, 8),
    prisma.recommendation.findMany({
      where: { organizationId, deletedAt: null },
      orderBy: { createdAt: "desc" },
      take: 12,
    }),
    prisma.recommendationWeight.findMany({
      where: { organizationId },
      take: 20,
    }),
  ]);

  return { properties, runs, recommendations, weights };
}

/**
 * Runs the cognitive loop and persists stage artifacts when a property exists.
 */
export async function executeAndPersistRun(input: {
  organizationId: string;
  propertyId: string;
  objective?: string;
}): Promise<{ result: PipelineRunResult; runId: string }> {
  const property = await prisma.visibilityProperty.findFirst({
    where: {
      id: input.propertyId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
    include: { competitors: { where: { deletedAt: null } }, keywords: true },
  });

  if (!property) {
    throw new Error("Visibility property not found");
  }

  const brand =
    (property.metadata as { brand?: string } | null)?.brand ?? property.name;

  const pipelineProperty: PipelineProperty = {
    id: property.id,
    organizationId: property.organizationId,
    name: property.name,
    brand,
    domain: property.primaryDomain,
    rootUrl: property.rootUrl,
    competitors: property.competitors.map((c) => ({
      name: c.name,
      domain: c.domain,
    })),
    keywords: property.keywords.map((k) => k.phrase),
  };

  const run = await prisma.intelligenceRun.create({
    data: {
      organizationId: input.organizationId,
      propertyId: property.id,
      status: "OBSERVING",
      trigger: "manual",
      objective: input.objective,
      startedAt: new Date(),
      currentStage: "OBSERVE",
    },
  });

  const weightsRows = await prisma.recommendationWeight.findMany({
    where: { organizationId: input.organizationId },
  });
  const weights = Object.fromEntries(
    weightsRows.map((w) => [`${w.kind}:${w.featureKey}`, w.weight]),
  );

  const result = await runIntelligencePipeline(pipelineProperty, { weights });

  await persistPipelineResult(
    run.id,
    input.organizationId,
    property.id,
    result,
  );

  return { result, runId: run.id };
}

async function persistPipelineResult(
  runId: string,
  organizationId: string,
  propertyId: string,
  result: PipelineRunResult,
) {
  const status =
    result.status === "COMPLETED"
      ? "COMPLETED"
      : result.status === "BLOCKED_ON_VERIFY"
        ? "BLOCKED_ON_VERIFY"
        : "FAILED";

  for (const stageName of Object.keys(result.stages) as Array<
    keyof typeof result.stages
  >) {
    const stage = result.stages[stageName];
    if (!stage) continue;
    await prisma.intelligenceStageResult.upsert({
      where: { runId_stage: { runId, stage: stageName } },
      create: {
        runId,
        stage: stageName,
        status:
          stage.status === "SUCCEEDED"
            ? "SUCCEEDED"
            : stage.status === "BLOCKED"
              ? "BLOCKED"
              : stage.status === "SKIPPED"
                ? "SKIPPED"
                : "FAILED",
        output: stage.output as object,
        confidence: stage.confidence,
        errorSummary: stage.errorSummary,
        startedAt: new Date(),
        completedAt: new Date(),
      },
      update: {
        status:
          stage.status === "SUCCEEDED"
            ? "SUCCEEDED"
            : stage.status === "BLOCKED"
              ? "BLOCKED"
              : stage.status === "SKIPPED"
                ? "SKIPPED"
                : "FAILED",
        output: stage.output as object,
        confidence: stage.confidence,
        errorSummary: stage.errorSummary,
        completedAt: new Date(),
      },
    });

    for (const trace of stage.traces) {
      await prisma.connectorTrace.create({
        data: {
          runId,
          stage: stageName,
          provider: trace.provider,
          role: trace.role,
          promptHash: trace.promptHash,
          model: trace.model,
          latencyMs: trace.latencyMs,
          tokenIn: trace.tokenIn,
          tokenOut: trace.tokenOut,
          success: true,
          responseMeta: {
            templateId: trace.templateId,
            simulated: trace.simulated,
            structured: (trace.structured ??
              null) as Prisma.InputJsonValue | null,
          } satisfies Prisma.InputJsonObject,
        },
      });
    }
  }

  if (result.decide?.recommendations.length) {
    for (const rec of result.decide.recommendations) {
      await prisma.recommendation.create({
        data: {
          organizationId,
          propertyId,
          runId,
          kind: rec.kind,
          title: rec.title,
          summary: rec.summary,
          rationale: rec.rationale,
          impactScore: rec.impactScore,
          effortScore: rec.effortScore,
          confidence: rec.confidence,
          priority:
            rec.impactScore * rec.confidence > 0.6
              ? "HIGH"
              : rec.impactScore > 0.4
                ? "MEDIUM"
                : "LOW",
          evidenceRefs: rec.evidenceRefs,
          payload: { features: rec.features },
        },
      });
    }
  }

  if (result.execute?.strategy) {
    await prisma.strategyPlan.create({
      data: {
        organizationId,
        propertyId,
        runId,
        title: result.execute.strategy.title,
        horizonDays: result.execute.strategy.horizonDays,
        summary: result.execute.strategy.summary,
        weeks: result.execute.strategy.weeks,
        status: "DRAFT",
      },
    });
  }

  if (result.measure?.scorecard) {
    for (const row of result.measure.scorecard.bySurface) {
      await prisma.aiVisibilitySample.create({
        data: {
          propertyId,
          surface: mapSurface(row.surface),
          prompt: "visibility_probe",
          promptHash: "measure.visibility_probe",
          mentionedBrand: row.mentionedBrand,
          citedUrl: row.citedUrl,
        },
      });
    }
  }

  if (result.learn?.weightUpdates.length) {
    for (const update of result.learn.weightUpdates) {
      const key = update.featureKey;
      const existing = await prisma.recommendationWeight.findUnique({
        where: {
          organizationId_kind_featureKey: {
            organizationId,
            kind: update.kind,
            featureKey: key,
          },
        },
      });
      if (existing) {
        await prisma.recommendationWeight.update({
          where: { id: existing.id },
          data: {
            weight: Math.max(
              0.2,
              Math.min(2.5, existing.weight + update.delta),
            ),
            sampleSize: existing.sampleSize + 1,
          },
        });
      } else {
        await prisma.recommendationWeight.create({
          data: {
            organizationId,
            kind: update.kind,
            featureKey: key,
            weight: 1 + update.delta,
            sampleSize: 1,
          },
        });
      }
    }

    for (const signal of result.learn.signals) {
      await prisma.learningSignal.create({
        data: {
          runId,
          signalKey: signal.key,
          value: signal.value,
        },
      });
    }
  }

  if (result.think?.graph) {
    for (const node of result.think.graph.nodes) {
      await prisma.knowledgeEntity.upsert({
        where: {
          propertyId_name_entityType: {
            propertyId,
            name: node.name,
            entityType: node.entityType,
          },
        },
        create: {
          propertyId,
          name: node.name,
          entityType: node.entityType,
          description: node.description,
        },
        update: {
          description: node.description,
        },
      });
    }
  }

  await prisma.intelligenceRun.update({
    where: { id: runId },
    data: {
      status,
      currentStage: "LEARN",
      confidence: result.confidence,
      summary: result.summary,
      completedAt: new Date(),
      errorSummary: result.status === "FAILED" ? result.summary : null,
    },
  });
}

function mapSurface(
  surface: string,
):
  | "CHATGPT"
  | "GEMINI"
  | "CLAUDE"
  | "PERPLEXITY"
  | "DEEPSEEK"
  | "GOOGLE_AI_OVERVIEW"
  | "OTHER" {
  if (
    surface === "CHATGPT" ||
    surface === "GEMINI" ||
    surface === "CLAUDE" ||
    surface === "PERPLEXITY" ||
    surface === "DEEPSEEK" ||
    surface === "GOOGLE_AI_OVERVIEW"
  ) {
    return surface;
  }
  return "OTHER";
}

/** In-memory demo run (no DB) for UI preview / tests of the loop shape */
export async function runDemoPipeline(
  overrides?: Partial<PipelineProperty>,
): Promise<PipelineRunResult> {
  const property: PipelineProperty = {
    id: "demo",
    organizationId: "demo-org",
    name: "Peacock One",
    brand: "Peacock One",
    domain: "peacock.one",
    rootUrl: "https://peacock.one",
    competitors: [{ name: "Generic SEO Suite", domain: "seo-suite.example" }],
    keywords: ["AI visibility", "AEO", "GEO"],
    ...overrides,
  };
  return runIntelligencePipeline(property);
}
