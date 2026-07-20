# Integrations contracts

Peacock One exposes provider-neutral integration surfaces. **Never commit real secrets.** Store credentials as vault references (`IntegrationCredentialReference.vaultRef`) or hashed values (`ApiKey.keyHash`, `WebhookEndpoint.secretHash`).

## API keys

- Create via Settings → Integrations or `POST /api/integrations/api-keys`.
- Plaintext secret is returned **once** at creation (`pk_live_…` / `pk_test_…`).
- Persist only `keyPrefix` + SHA-256 `keyHash`.
- Scopes: `read:crm`, `write:crm`, `read:finance`, `write:finance`, `read:hr`, `webhooks:manage`, `imports:write`, `exports:read`.
- Support expiry, revocation, and `lastUsedAt` updates on successful auth.

## Webhooks

- Endpoints store URL, event list, and hashed signing secret.
- Deliveries record attempts, response codes, failure messages, and retry schedule (`nextWebhookRetryAt`).
- Signature header: `x-peacock-signature: t=<unix>,v1=<sha256(secret.timestamp.payload)>`.

## Email

Provider adapters (selected via `EMAIL_PROVIDER`, default preview in development):

| Provider | Adapter | Notes |
| --- | --- | --- |
| Preview | `preview` | Dev/test — no external delivery |
| SMTP | `smtp` | Requires `SMTP_*` env vars |
| Google Workspace | `google_workspace` | Vault OAuth reference required |
| Microsoft 365 | `microsoft_365` | Vault OAuth reference required |
| Transactional | `transactional` | Vendor API key via vault |

Templates live in `emails/templates.ts` with `{{variable}}` substitution. Send logs capture delivery/failure status, attempts, and preview mode.

**Do not claim live delivery works until credentials are configured and an integration test succeeds.**

## Calendar

Adapters: Google Calendar, Microsoft Outlook Calendar (`modules/calendar`).

Planned sync entity types:

- `crm_meeting`
- `interview`
- `leave`
- `project_deadline`
- `follow_up`

Until a `CalendarConnection` has a vault credential and an integration test passes, providers report `DISCONNECTED` and sync must not be advertised as working.

## Import / export

CSV import entities and export datasets are catalogued in `modules/imports` and `modules/exports`. Authorization is enforced server-side; sensitive export columns require elevated permissions and may need approval.

## Document centre

`/documents` uses `ObjectStorage` (`lib/storage.ts`) for upload/download. Access respects visibility, grants, expiry, and download audit logs.

---

## Extension points

### Website lead forms

**Ingress:** `POST` signed webhook or API key with scope `write:crm`.

```json
{
  "event": "lead.created",
  "payload": {
    "fullName": "string",
    "email": "string",
    "company": "string?",
    "source": "website_form",
    "metadata": {}
  }
}
```

Map into CRM lead create; emit `lead.created` webhook outbound for subscribers.

### Google Workspace

**Capabilities:** directory sync (optional), mailbox send via `google_workspace` email adapter, calendar via Google calendar provider.

**Auth:** OAuth refresh token stored as `vaultRef` only.

**Status gate:** disconnected until credentials + integration test succeed.

### Accounting software

**Outbound:** invoice create/update, payment applied.

**Inbound webhook events:** `invoice.paid`, `bill.received`.

**Contract fields:** externalId, currency, amountMinor, issueDate, dueDate.

### Payment gateways

**Ingress webhook:** payment intent succeeded/failed with idempotency key.

**Scopes:** none on browser; server verifies gateway signature using vault secret reference.

### Attendance systems

**Ingress:** CSV import entity `attendance` or webhook `attendance.punch`.

```json
{
  "employeeCode": "string",
  "occurredAt": "ISO-8601",
  "type": "IN" | "OUT"
}
```

### Cloud storage

Implement `ObjectStorage` for S3-compatible providers. Configure via `S3_*` env vars — never hard-code keys.

### Messaging platforms

Notification adapter interface (future): `notify(channel, message)`.

Outbound events may fan into Slack/Teams after vault bot tokens are configured.

---

## Security checklist

1. No plaintext secrets in git, logs, or audit metadata beyond prefixes.
2. API key verification uses constant-time hash compare.
3. Export downloads expire; document downloads are audited.
4. Calendar/email providers fail closed when unconfigured.
