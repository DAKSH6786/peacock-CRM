export {
  API_KEY_SCOPES,
  generateApiKey,
  hashApiKey,
  verifyApiKey,
  isApiKeyUsable,
  apiKeyHasScope,
  generateWebhookSigningSecret,
  signWebhookPayload,
  nextWebhookRetryAt,
} from "./api-keys";
export type { ApiKeyScope, GeneratedApiKey } from "./api-keys";

export type IntegrationExtensionPoint =
  | "website_lead_forms"
  | "google_workspace"
  | "accounting_software"
  | "payment_gateways"
  | "attendance_systems"
  | "cloud_storage"
  | "messaging_platforms";

export const INTEGRATION_EXTENSION_POINTS: Array<{
  id: IntegrationExtensionPoint;
  label: string;
  description: string;
  contractDoc: string;
}> = [
  {
    id: "website_lead_forms",
    label: "Website lead forms",
    description: "Inbound lead capture via signed webhook or API key.",
    contractDoc: "docs/integrations.md#website-lead-forms",
  },
  {
    id: "google_workspace",
    label: "Google Workspace",
    description: "Directory, calendar, and mailbox adapters (credentials required).",
    contractDoc: "docs/integrations.md#google-workspace",
  },
  {
    id: "accounting_software",
    label: "Accounting software",
    description: "Invoice and payment sync contracts.",
    contractDoc: "docs/integrations.md#accounting-software",
  },
  {
    id: "payment_gateways",
    label: "Payment gateways",
    description: "Payment confirmation webhooks.",
    contractDoc: "docs/integrations.md#payment-gateways",
  },
  {
    id: "attendance_systems",
    label: "Attendance systems",
    description: "Punch import and daily attendance feeds.",
    contractDoc: "docs/integrations.md#attendance-systems",
  },
  {
    id: "cloud_storage",
    label: "Cloud storage",
    description: "Object storage providers behind ObjectStorage.",
    contractDoc: "docs/integrations.md#cloud-storage",
  },
  {
    id: "messaging_platforms",
    label: "Messaging platforms",
    description: "Slack/Teams notification adapters.",
    contractDoc: "docs/integrations.md#messaging-platforms",
  },
];
