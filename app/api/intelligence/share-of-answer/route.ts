import { NextResponse } from "next/server";
import { z } from "zod";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  aggregateBrandScores,
  assertNotTokenOnlyWeights,
  shareOfAnswerCatalog,
  type EntityIndicatorReading,
} from "@/modules/share-of-answer";
import { requirePermission } from "@/permissions";

const readingSchema = z.object({
  entityName: z.string().min(1),
  isClient: z.boolean().optional(),
  mention: z.boolean(),
  mentionCount: z.number().int().optional(),
  position: z.number().int().nullable().optional(),
  recommendationStrength: z.number().min(0).max(1),
  answerSpace: z.number().min(0).max(1),
  citationOwnership: z.number().min(0).max(1),
  semanticProminence: z.number().min(0).max(1),
  positiveClaims: z.number().int().min(0),
  negativeClaims: z.number().int().min(0),
  neutralClaims: z.number().int().min(0),
  comparisonOutcome: z.string(),
  tokenSpanRatio: z.number().min(0).max(1),
});

const bodySchema = z.object({
  queryCluster: z.string().min(1).max(255),
  clientBrand: z.string().min(1).max(255),
  observations: z.array(z.array(readingSchema)).min(1),
  indicatorWeights: z.record(z.string(), z.number()).optional(),
});

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "intelligence:view");
    return NextResponse.json(shareOfAnswerCatalog());
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unauthorized";
    return NextResponse.json({ error: message }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "intelligence:run");

    const body = bodySchema.parse(await request.json());
    if (body.indicatorWeights) {
      assertNotTokenOnlyWeights(body.indicatorWeights);
    }

    const brands = aggregateBrandScores(
      body.observations as EntityIndicatorReading[][],
      body.indicatorWeights,
    );

    return NextResponse.json({
      queryCluster: body.queryCluster,
      clientBrand: body.clientBrand,
      methodology: "multi_indicator",
      tokenCountAloneRejected: true,
      brands,
      exampleDisplay: brands.map((b) => ({
        brand: b.entityName,
        shareOfAnswerPct: Math.round(b.shareOfAnswer * 10) / 10,
        isClient: b.isClient,
      })),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to score Share of Answer";
    const status = message.includes("permission") ? 403 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
