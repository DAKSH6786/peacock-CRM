import { tryGetServerEnv } from "@/lib/env";

import {
  GoogleWorkspaceEmailProvider,
  Microsoft365EmailProvider,
  PreviewEmailProvider,
  SmtpEmailProvider,
  TransactionalEmailProvider,
} from "./adapters";
import type { EmailProvider, EmailProviderKind } from "./types";

export function createEmailProvider(
  kind?: EmailProviderKind,
): EmailProvider {
  const env = tryGetServerEnv();
  const previewForced =
    process.env.EMAIL_PREVIEW_MODE === "true" ||
    process.env.NODE_ENV === "development" ||
    process.env.NODE_ENV === "test";

  const selected =
    kind ??
    (process.env.EMAIL_PROVIDER as EmailProviderKind | undefined) ??
    (previewForced ? "preview" : "smtp");

  if (selected === "preview" || previewForced) {
    return new PreviewEmailProvider();
  }

  switch (selected) {
    case "smtp":
      return new SmtpEmailProvider({
        host: env?.SMTP_HOST ?? process.env.SMTP_HOST,
        port: env?.SMTP_PORT ?? (process.env.SMTP_PORT ? Number(process.env.SMTP_PORT) : undefined),
        user: env?.SMTP_USER ?? process.env.SMTP_USER,
        password: env?.SMTP_PASSWORD ?? process.env.SMTP_PASSWORD,
        from: env?.SMTP_FROM ?? process.env.SMTP_FROM,
      });
    case "google_workspace":
      return new GoogleWorkspaceEmailProvider();
    case "microsoft_365":
      return new Microsoft365EmailProvider();
    case "transactional":
      return new TransactionalEmailProvider();
    default:
      return new PreviewEmailProvider();
  }
}

export type { EmailProvider, EmailProviderKind, SendEmailInput, SendEmailResult } from "./types";
export {
  PreviewEmailProvider,
  SmtpEmailProvider,
  GoogleWorkspaceEmailProvider,
  Microsoft365EmailProvider,
  TransactionalEmailProvider,
} from "./adapters";
