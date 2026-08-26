import { NextResponse } from "next/server";
import { z } from "zod";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  PROMPT_SOURCE_KINDS,
  expandPromptUniverse,
  promptUniverseCatalog,
} from "@/modules/prompt-universe";
import { requirePermission } from "@/permissions";

const signalSchema = z.object({
  sourceKind: z.enum(PROMPT_SOURCE_KINDS),
  signalText: z.string().min(1).max(4000),
  weight: z.number().min(0).max(5).optional(),
  locationCode: z.string().max(64).optional(),
  productName: z.string().max(255).optional(),
  topicHint: z.string().max(255).optional(),
});

const bodySchema = z.object({
  brandName: z.string().min(1).max(255),
  industry: z.string().max(128).optional(),
  location: z.string().max(64).optional(),
  personaCodes: z.array(z.string()).optional(),
  includePersonaVariants: z.boolean().optional(),
  maxPrompts: z.number().int().min(1).max(5000).optional(),
  signals: z.array(signalSchema).min(1),
});

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "intelligence:view");
    return NextResponse.json(promptUniverseCatalog());
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
    const result = expandPromptUniverse(body);

    return NextResponse.json({
      promptCount: result.prompts.length,
      familyCount: result.familyCount,
      simpleCount: result.simpleCount,
      contextualCount: result.contextualCount,
      tracksBothSimpleAndContextual: true,
      prompts: result.prompts.slice(0, 100),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to expand universe";
    const status = message.includes("permission") ? 403 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
