# Entity-relationship diagram (Peacock One)

Relational schema for the architecture stage. Embeddings use **pgvector** inside PostgreSQL.

## Cascade policy (careful defaults)

| Child | Parent | ON DELETE | Rationale |
| --- | --- | --- | --- |
| `workspaces` | `organisations` | **CASCADE** | Workspace cannot outlive its tenant |
| `roles` | `organisations` | **CASCADE** | Org-scoped roles |
| `memberships` | `organisations` | **CASCADE** | Tenant membership |
| `memberships` | `users` | **CASCADE** | Remove membership when user is deleted |
| `memberships` | `roles` | **RESTRICT** | Do not delete a role still assigned to users |
| `workspace_memberships` | `organisations` / `workspaces` / `users` | **CASCADE** | Pure join ownership |
| `workspace_memberships` | `roles` | **RESTRICT** | Protect in-use roles |
| `role_permissions` | `roles` / `permissions` | **CASCADE** | Join rows are disposable |
| `background_jobs` | `organisations` | **CASCADE** | Tenant wipe |
| `background_jobs` | `workspaces` | **SET NULL** | Preserve job history if workspace removed |
| `background_jobs` | `users` (creator) | **SET NULL** | Preserve job history if user removed |
| `audit_logs` | `organisations` | **CASCADE** | Tenant wipe |
| `audit_logs` | `users` (actor) | **SET NULL** | Keep audit row; anonymise actor |
| `audit_logs` | `workspaces` | **SET NULL** | Keep audit row |
| `audit_log_attributes` | `audit_logs` | **CASCADE** | Attributes owned by the log |
| `embedding_chunks` | `organisations` | **CASCADE** | Tenant wipe |
| `embedding_chunks` | `workspaces` | **SET NULL** | Keep chunk if workspace removed |
| `embedding_chunk_attributes` | `embedding_chunks` | **CASCADE** | Attributes owned by the chunk |
| `ai_provider_models` | `ai_providers` | **CASCADE** | Catalog hierarchy |

## JSONB policy

JSONB is used **only** where the shape is genuinely job-specific and heterogeneous:

- `background_jobs.payload`
- `background_jobs.result`

Everything else that looks like “metadata” is modelled relationally:

- `audit_log_attributes (audit_log_id, key, value)`
- `embedding_chunk_attributes (chunk_id, key, value)`
- Structured columns on `embedding_chunks`: `content_hash`, `embedding_model`, `token_count`
- `ai_provider_models` instead of a JSON array of models on the provider

## Mermaid ERD

```mermaid
erDiagram
    organisations ||--o{ workspaces : has
    organisations ||--o{ roles : has
    organisations ||--o{ memberships : has
    organisations ||--o{ workspace_memberships : has
    organisations ||--o{ background_jobs : owns
    organisations ||--o{ audit_logs : owns
    organisations ||--o{ embedding_chunks : owns

    users ||--o{ memberships : has
    users ||--o{ workspace_memberships : has
    users ||--o{ background_jobs : created_by
    users ||--o{ audit_logs : actor

    roles ||--o{ memberships : assigned
    roles ||--o{ workspace_memberships : assigned
    roles ||--o{ role_permissions : grants
    permissions ||--o{ role_permissions : granted_by

    workspaces ||--o{ workspace_memberships : has
    workspaces ||--o{ background_jobs : scopes
    workspaces ||--o{ audit_logs : scopes
    workspaces ||--o{ embedding_chunks : scopes

    audit_logs ||--o{ audit_log_attributes : has
    embedding_chunks ||--o{ embedding_chunk_attributes : has

    ai_providers ||--o{ ai_provider_models : offers

    organisations {
        string id PK
        string name
        string slug UK
        bool is_active
    }

    users {
        string id PK
        string email UK
        string hashed_password
        string google_sub UK
        string microsoft_sub UK
    }

    workspaces {
        string id PK
        string organisation_id FK
        string slug
    }

    roles {
        string id PK
        string organisation_id FK
        string code
    }

    permissions {
        string id PK
        string code UK
    }

    role_permissions {
        string id PK
        string role_id FK
        string permission_id FK
    }

    memberships {
        string id PK
        string organisation_id FK
        string user_id FK
        string role_id FK
    }

    workspace_memberships {
        string id PK
        string organisation_id FK
        string workspace_id FK
        string user_id FK
        string role_id FK
    }

    background_jobs {
        string id PK
        string organisation_id FK
        string workspace_id FK
        string created_by_user_id FK
        string name
        string status
        jsonb payload
        jsonb result
    }

    audit_logs {
        string id PK
        string organisation_id FK
        string actor_user_id FK
        string workspace_id FK
        string action
        string resource_type
        string resource_id
    }

    audit_log_attributes {
        string id PK
        string audit_log_id FK
        string key
        string value
    }

    embedding_chunks {
        string id PK
        string organisation_id FK
        string workspace_id FK
        string source_type
        string source_id
        string content_hash
        string embedding_model
        int token_count
        vector embedding
    }

    embedding_chunk_attributes {
        string id PK
        string chunk_id FK
        string key
        string value
    }

    ai_providers {
        string id PK
        string code UK
        string name
        string vendor
        bool is_active
    }

    ai_provider_models {
        string id PK
        string provider_id FK
        string model_code
        string display_name
        bool is_default
    }
```

## Seeded AI providers

| Code | Display name | Vendor |
| --- | --- | --- |
| `openai` | OpenAI | OpenAI |
| `gemini` | Gemini | Google |
| `anthropic` | Claude | Anthropic |
| `perplexity` | Perplexity | Perplexity |
| `deepseek` | DeepSeek | DeepSeek |

Seeded via `infra/scripts/seed_dev.py` using `db_models.provider_seed.SUPPORTED_AI_PROVIDERS`.
