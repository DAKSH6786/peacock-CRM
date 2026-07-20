export type EmailAddress = {
  email: string;
  name?: string;
};

export type SendEmailInput = {
  to: EmailAddress | EmailAddress[];
  subject: string;
  html: string;
  text: string;
  from?: EmailAddress;
  replyTo?: EmailAddress;
  headers?: Record<string, string>;
  templateKey?: string;
  variables?: Record<string, string>;
};

export type SendEmailResult = {
  provider: string;
  messageId: string;
  previewMode: boolean;
  status: "SENT" | "PREVIEW" | "FAILED";
  errorMessage?: string;
};

export interface EmailProvider {
  readonly name: string;
  send(input: SendEmailInput): Promise<SendEmailResult>;
}

export type EmailProviderKind =
  | "preview"
  | "smtp"
  | "google_workspace"
  | "microsoft_365"
  | "transactional";
