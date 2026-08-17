# Security for AI Connectors

Treat LLM input/output as **untrusted**.

## Policy

> Website content must never be able to instruct PINE to expose secrets or change system behaviour.
>
> **Crawler-extracted content is DATA. It is not trusted instructions.**

## Controls

| Control | Purpose |
| --- | --- |
| Prompt injection detection | Heuristics for ignore-instructions / reveal-secrets / behaviour-change |
| Content isolation | Trust tiers; crawler body = `untrusted_data`, never instructions |
| Tool permissions | Fail-closed scopes (`secret_read` never from content) |
| Connector permissions | Only granted connectors may run |
| URL safety | Block private/localhost/metadata and non-http(s) schemes |
| PII handling | Detect + redact email/phone/SSN-like before context use |
| Tenant boundaries | Organisation/workspace claim must match AuthContext |
| Output validation | No secrets, no instruction-channel leak, structured summary |

## Demo verdict

Malicious HTML in a crawled page attempting “ignore previous instructions / reveal system prompt” is **quarantined** as data. PINE does not adopt it as system behaviour.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/ai-connector-security/catalog` | Controls, trust tiers, patterns |
| `GET` | `/ai-connector-security/preview` | Demo scan (injection blocked) |
| `POST` | `/ai-connector-security/scans` | Persist a security scan |
| `GET` | `/ai-connector-security/scans/{id}` | Retrieve scan |

## Tables

`ai_connector_security_scans`, `acs_content_segments`, `acs_injection_findings`, `acs_permission_checks`, `acs_url_safety_checks`, `acs_pii_findings`, `acs_output_validations`, `acs_control_activations`
