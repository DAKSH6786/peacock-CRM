# Peacock Action Engine

Approval-based **autonomous execution layer** — moves Peacock One beyond recommendations.

## Status lifecycle

`DRAFT` → `APPROVAL_REQUIRED` → `APPROVED` → `EXECUTED` | `FAILED` | `REVERTED`

## Actions

| Code | Label |
| --- | --- |
| `create_task` | Create task |
| `assign_writer` | Assign writer |
| `generate_brief` | Generate brief |
| `notify_editor` | Notify editor |
| `schedule_recrawl` | Schedule recrawl |
| `generate_schema_suggestion` | Generate schema suggestion |
| `prepare_internal_linking_plan` | Prepare internal linking plan |
| `create_outreach_prospect` | Create outreach prospect |
| `generate_report` | Generate report |
| `schedule_monitoring` | Schedule monitoring |
| `cms_draft_change` | CMS draft change (future connector) |
| `cms_publish` | CMS publish (future connector — destructive) |

Future connectors may support CMS changes.

## Guardrail

**Never make destructive external modifications without explicit permissions.**

Destructive / CMS actions stay in `DRAFT` until a matching connector permission is granted (`cms_write`, `cms_publish`). Execution without permission fails closed.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/actions/catalog` | Types, statuses, guardrail |
| `POST` | `/actions` | Create action |
| `GET` | `/actions/{id}` | Retrieve |
| `POST` | `/actions/{id}/submit` | Submit for approval |
| `POST` | `/actions/{id}/approve` | Approve |
| `POST` | `/actions/{id}/reject` | Reject → DRAFT |
| `POST` | `/actions/{id}/execute` | Execute (approved only) |
| `POST` | `/actions/{id}/revert` | Revert executed action |
| `POST` | `/actions/permissions/grant` | Grant connector permission |

## Tables

`peacock_actions`, `pae_connector_permissions`, `pae_approvals`, `pae_executions`, `pae_status_events`
