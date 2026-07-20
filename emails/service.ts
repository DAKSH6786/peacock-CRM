import "server-only";

import { prisma } from "@/database";
import { createEmailProvider } from "@/emails/providers";
import type { SendEmailInput } from "@/emails/providers";
import { getSystemTemplate, renderTemplate } from "@/emails/templates";

const MAX_ATTEMPTS = 3;

export async function sendTemplatedEmail(input: {
  organizationId: string;
  to: string;
  templateKey: string;
  variables?: Record<string, string>;
  sentById?: string | null;
  providerKind?: Parameters<typeof createEmailProvider>[0];
}) {
  const template = getSystemTemplate(input.templateKey);
  if (!template) {
    throw new Error(`Unknown email template: ${input.templateKey}`);
  }

  const rendered = renderTemplate(template, input.variables ?? {});
  return sendAndLogEmail({
    organizationId: input.organizationId,
    sentById: input.sentById,
    templateKey: input.templateKey,
    message: {
      to: { email: input.to },
      subject: rendered.subject,
      html: rendered.html,
      text: rendered.text,
      templateKey: input.templateKey,
      variables: input.variables,
    },
    providerKind: input.providerKind,
  });
}

export async function sendAndLogEmail(input: {
  organizationId: string;
  sentById?: string | null;
  templateKey?: string;
  message: SendEmailInput;
  providerKind?: Parameters<typeof createEmailProvider>[0];
}) {
  const provider = createEmailProvider(input.providerKind);
  const toAddress = Array.isArray(input.message.to)
    ? input.message.to.map((t) => t.email).join(",")
    : input.message.to.email;

  const log = await prisma.emailSendLog.create({
    data: {
      organizationId: input.organizationId,
      provider: provider.name,
      templateKey: input.templateKey ?? input.message.templateKey ?? null,
      toAddress,
      subject: input.message.subject,
      status: "QUEUED",
      attempts: 0,
      previewMode: provider.name === "preview",
      payload: {
        variables: input.message.variables ?? {},
      },
      sentById: input.sentById ?? null,
    },
  });

  let attempts = 0;
  let lastError: string | undefined;

  while (attempts < MAX_ATTEMPTS) {
    attempts += 1;
    try {
      const result = await provider.send(input.message);
      const status =
        result.status === "PREVIEW"
          ? "PREVIEW"
          : result.status === "SENT"
            ? "SENT"
            : "FAILED";

      await prisma.emailSendLog.update({
        where: { id: log.id },
        data: {
          status,
          attempts,
          providerMessageId: result.messageId || null,
          errorMessage: result.errorMessage ?? null,
          previewMode: result.previewMode,
          sentAt: status === "FAILED" ? null : new Date(),
        },
      });

      if (status !== "FAILED") {
        return { logId: log.id, ...result };
      }
      lastError = result.errorMessage;
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Unknown send error";
      await prisma.emailSendLog.update({
        where: { id: log.id },
        data: {
          status: "FAILED",
          attempts,
          errorMessage: lastError,
        },
      });
    }
  }

  return {
    logId: log.id,
    provider: provider.name,
    messageId: "",
    previewMode: provider.name === "preview",
    status: "FAILED" as const,
    errorMessage: lastError,
  };
}
