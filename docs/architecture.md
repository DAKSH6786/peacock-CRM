# Peacock One architecture

Peacock One is a **modular monolith** built with Next.js App Router. Business domains live under `modules/`, shared infrastructure under `lib/`, `server/`, `database/`, `jobs/`, `emails/`, `permissions/`, and `validations/`.

## Principles

- Every major business record includes `organizationId` for future multi-tenant support.
- Monetary values are stored as integer minor units.
- Timestamps are stored in UTC and displayed in the organization timezone.
- Important records support soft deletion via `deletedAt`.
- Sensitive mutations write audit-log entries.
- Authorization is enforced in server-side permission checks, not only in the UI.

## Layers

1. **UI** — `app/` routes and `components/`
2. **Validation** — Zod schemas in `validations/` and module folders
3. **Permissions** — `permissions/` role-to-capability mapping
4. **Services** — `modules/*/service.ts` business logic
5. **Data** — Prisma models in `prisma/schema.prisma`, client in `database/`
6. **Jobs** — `jobs/` queue abstraction for async work
7. **Storage** — `lib/storage.ts` S3-compatible abstraction

## Next extraction path

Modules can later become services by extracting their service layer, schema slice, and jobs while keeping the same permission and audit contracts.
