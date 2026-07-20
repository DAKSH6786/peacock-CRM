export type EmailTemplate = {
  key: string;
  subject: string;
  html: string;
  text: string;
};

export type TemplateVariableMap = Record<string, string>;

export function renderTemplate(
  template: EmailTemplate,
  variables: TemplateVariableMap,
): EmailTemplate {
  const replace = (input: string) =>
    input.replace(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g, (_, key: string) => {
      return variables[key] ?? "";
    });

  return {
    key: template.key,
    subject: replace(template.subject),
    html: replace(template.html),
    text: replace(template.text),
  };
}

export function passwordResetEmail(params: {
  name?: string | null;
  resetUrl: string;
}): EmailTemplate {
  const greeting = params.name ? `Hi ${params.name},` : "Hi,";
  const text = `${greeting}\n\nReset your Peacock One password:\n${params.resetUrl}\n\nIf you did not request this, ignore this email.`;
  const html = `<p>${greeting}</p><p><a href="${params.resetUrl}">Reset your Peacock One password</a></p><p>If you did not request this, ignore this email.</p>`;

  return {
    key: "password_reset",
    subject: "Reset your Peacock One password",
    html,
    text,
  };
}

export function welcomeEmail(params: {
  name?: string | null;
  loginUrl: string;
}): EmailTemplate {
  const greeting = params.name ? `Welcome, ${params.name}.` : "Welcome.";
  return {
    key: "welcome",
    subject: "Welcome to Peacock One",
    text: `${greeting}\n\nSign in at ${params.loginUrl}`,
    html: `<p>${greeting}</p><p><a href="${params.loginUrl}">Sign in to Peacock One</a></p>`,
  };
}

export const SYSTEM_EMAIL_TEMPLATES: EmailTemplate[] = [
  {
    key: "import_complete",
    subject: "Import complete: {{entityLabel}}",
    text: "Your {{entityLabel}} import finished. {{successRows}} succeeded, {{failedRows}} failed.",
    html: "<p>Your <strong>{{entityLabel}}</strong> import finished.</p><p>{{successRows}} succeeded, {{failedRows}} failed.</p>",
  },
  {
    key: "export_ready",
    subject: "Export ready: {{exportLabel}}",
    text: "Your {{exportLabel}} export is ready. Download before {{expiresAt}}.",
    html: "<p>Your <strong>{{exportLabel}}</strong> export is ready.</p><p>Download before {{expiresAt}}.</p>",
  },
  {
    key: "export_approval_needed",
    subject: "Export approval needed: {{exportLabel}}",
    text: "{{requester}} requested a sensitive {{exportLabel}} export.",
    html: "<p><strong>{{requester}}</strong> requested a sensitive <strong>{{exportLabel}}</strong> export.</p>",
  },
];

export function getSystemTemplate(key: string): EmailTemplate | undefined {
  return SYSTEM_EMAIL_TEMPLATES.find((t) => t.key === key);
}
