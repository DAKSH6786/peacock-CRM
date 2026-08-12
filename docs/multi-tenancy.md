# Multi-tenancy

## Hierarchy

```text
Organisation
  └── Workspace(s)
        └── Membership-scoped resources
User ── Membership(role) ──► Organisation
User ── WorkspaceMembership ──► Workspace
```

## Isolation rules

- Every tenant-owned row includes `organisation_id`.
- API handlers resolve `AuthContext` from JWT (`sub`, `org`, `ws`).
- Workspace access is rejected when `workspace.organisation_id != token.org`.
- Job payloads always carry `organisation_id`; workers must re-check before writes.
- Never return cross-org records from list endpoints (enforce in queries, not UI).

## Roles & permissions

- Org roles: `owner`, `admin`, `member`, `viewer` (seed/register creates `owner`).
- `permissions` table is global capability catalog; org roles map later.
- OAuth subjects (`google_sub`, `microsoft_sub`) prepared on `users`.
