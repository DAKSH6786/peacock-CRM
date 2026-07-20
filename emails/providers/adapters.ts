import type {
  EmailProvider,
  SendEmailInput,
  SendEmailResult,
} from "./types";

/**
 * Development preview provider — never delivers externally.
 * Logs are persisted by the email service layer.
 */
export class PreviewEmailProvider implements EmailProvider {
  readonly name = "preview";

  async send(input: SendEmailInput): Promise<SendEmailResult> {
    void input;
    return {
      provider: this.name,
      messageId: `preview_${crypto.randomUUID()}`,
      previewMode: true,
      status: "PREVIEW",
      errorMessage: undefined,
    };
  }
}

/**
 * SMTP adapter stub. Requires SMTP_* env vars — does not claim delivery
 * until credentials are configured and an integration test succeeds.
 */
export class SmtpEmailProvider implements EmailProvider {
  readonly name = "smtp";

  constructor(
    private readonly config: {
      host?: string;
      port?: number;
      user?: string;
      password?: string;
      from?: string;
    },
  ) {}

  async send(_input: SendEmailInput): Promise<SendEmailResult> {
    if (!this.config.host || !this.config.from) {
      return {
        provider: this.name,
        messageId: "",
        previewMode: false,
        status: "FAILED",
        errorMessage:
          "SMTP is not configured. Set SMTP_HOST and SMTP_FROM (never commit secrets).",
      };
    }

    // Transport wiring lives behind env-configured credentials.
    // Until an integration test succeeds, treat as not ready.
    return {
      provider: this.name,
      messageId: "",
      previewMode: false,
      status: "FAILED",
      errorMessage:
        "SMTP adapter is installed but live delivery is disabled until credentials and an integration test succeed.",
    };
  }
}

export class GoogleWorkspaceEmailProvider implements EmailProvider {
  readonly name = "google_workspace";

  async send(_input: SendEmailInput): Promise<SendEmailResult> {
    return {
      provider: this.name,
      messageId: "",
      previewMode: false,
      status: "FAILED",
      errorMessage:
        "Google Workspace email requires a vault credential reference and a passing integration test.",
    };
  }
}

export class Microsoft365EmailProvider implements EmailProvider {
  readonly name = "microsoft_365";

  async send(_input: SendEmailInput): Promise<SendEmailResult> {
    return {
      provider: this.name,
      messageId: "",
      previewMode: false,
      status: "FAILED",
      errorMessage:
        "Microsoft 365 email requires a vault credential reference and a passing integration test.",
    };
  }
}

export class TransactionalEmailProvider implements EmailProvider {
  readonly name = "transactional";

  async send(_input: SendEmailInput): Promise<SendEmailResult> {
    return {
      provider: this.name,
      messageId: "",
      previewMode: false,
      status: "FAILED",
      errorMessage:
        "Transactional provider requires API credentials via vault reference — not configured.",
    };
  }
}
