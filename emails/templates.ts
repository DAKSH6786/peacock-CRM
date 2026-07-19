export type EmailTemplate = {
  subject: string;
  html: string;
  text: string;
};

export function passwordResetEmail(params: {
  name?: string | null;
  resetUrl: string;
}): EmailTemplate {
  const greeting = params.name ? `Hi ${params.name},` : "Hi,";
  const text = `${greeting}\n\nReset your Peacock One password:\n${params.resetUrl}\n\nIf you did not request this, ignore this email.`;
  const html = `<p>${greeting}</p><p><a href="${params.resetUrl}">Reset your Peacock One password</a></p><p>If you did not request this, ignore this email.</p>`;

  return {
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
    subject: "Welcome to Peacock One",
    text: `${greeting}\n\nSign in at ${params.loginUrl}`,
    html: `<p>${greeting}</p><p><a href="${params.loginUrl}">Sign in to Peacock One</a></p>`,
  };
}
