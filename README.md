# Peacock One

Peacock One is the internal business operating system for **Digital Peacock**. It consolidates CRM, sales, delivery ERP, XYME goal management, HRMS, finance, documents, approvals, reporting, and audit into one modular monolith.

## Stack

- Next.js (App Router) + TypeScript (strict)
- PostgreSQL + Prisma ORM
- Auth.js (NextAuth v5)
- Tailwind CSS + premium Peacock OS UI (dark-default, light mode supported)
- Manrope + Source Sans 3
- React Hook Form + Zod
- TanStack Table + Recharts
- S3-compatible storage abstraction
- Background job abstraction
- Vitest + Playwright
- Docker Compose for local infrastructure

See [`docs/design-system.md`](./docs/design-system.md) for UI tokens and interaction rules.  
See [`docs/database-model.md`](./docs/database-model.md) for the full entity relationship model.

## Prerequisites

- Node.js 22+
- npm 10+
- Docker (recommended for PostgreSQL and MinIO)

## Quick start

```bash
# 1. Install dependencies
npm install

# 2. Copy environment variables
cp .env.example .env

# 3. Start PostgreSQL (+ optional MinIO)
docker compose up -d db minio

# 4. Generate Prisma client and run migrations
npm run db:generate
npm run db:migrate

# 5. Seed the Digital Peacock organization + admin user
npm run db:seed

# 6. Start the app
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Default seed credentials (override via `.env`):

- Email: `admin@digitalpeacock.local`
- Password: `ChangeMeNow!123`

## Scripts

| Script                      | Purpose                            |
| --------------------------- | ---------------------------------- |
| `npm run dev`               | Development server (Turbopack)     |
| `npm run build`             | Prisma generate + production build |
| `npm run start`             | Start production server            |
| `npm run lint`              | ESLint                             |
| `npm run format`            | Prettier write                     |
| `npm run typecheck`         | TypeScript `--noEmit`              |
| `npm run test`              | Vitest unit tests                  |
| `npm run test:e2e`          | Playwright end-to-end tests        |
| `npm run db:migrate`        | Create/apply migrations (dev)      |
| `npm run db:migrate:deploy` | Apply migrations (prod)            |
| `npm run db:seed`           | Seed demo/org bootstrap data       |
| `npm run db:studio`         | Prisma Studio                      |
| `npm run check:env`         | Validate environment variables     |
| `docker compose up`         | App + Postgres + MinIO             |

## Project structure

```text
app/            Next.js App Router routes & API handlers
components/     Shared UI and layout
modules/        Domain modules (CRM, HR, finance, …)
lib/            Env, utils, storage abstractions
server/         Server-only helpers
database/       Prisma client singleton
jobs/           Background job queue abstraction
emails/         Email templates
permissions/    Role → permission checks
validations/    Shared Zod schemas
tests/          Unit and e2e tests
scripts/        Operational scripts
prisma/         Schema, migrations, seed
docs/           Architecture notes
```

## Authentication & access control

- Credentials provider via Auth.js
- JWT sessions with organization + role claims
- Middleware protects application routes
- Server-side `requirePermission` checks for sensitive operations
- Audit logging for login and (later) all sensitive mutations

## Health check

`GET /api/health` returns service status and a database connectivity check.

## Environment variables

See [`.env.example`](./.env.example) for the full list. At minimum you must configure:

- `DATABASE_URL`
- `AUTH_SECRET` (≥ 32 characters)
- `APP_URL` / `AUTH_URL`

Optional for later features:

- `S3_*` for object storage
- `SMTP_*` for outbound email
- `JOBS_ENABLED`
- `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`

## Docker

```bash
# Infrastructure only
docker compose up -d db minio

# Full stack (build + run app)
docker compose up --build
```

## Testing

```bash
npm run typecheck
npm run lint
npm run test
npm run build

# E2E (requires a running or auto-started server)
npm run test:e2e
```

## License

Proprietary — Digital Peacock internal use.
