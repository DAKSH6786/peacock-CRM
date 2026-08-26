# Peacock One architecture

Peacock One is a **modular monolith** built with Next.js App Router.

Its differentiating product capability is **SEO + AEO + GEO Search & Generative Visibility Intelligence**, orchestrated by the cognitive loop:

```text
OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN
```

Business OS domains (CRM, delivery, finance, HR, XYME) remain available as the operating layer. Visibility intelligence is first-class — not an LLM chat wrapper.

See also:

- [`docs/product-philosophy.md`](./product-philosophy.md)
- [`docs/intelligence-architecture.md`](./intelligence-architecture.md)

## Principles

- Every major business record includes `organizationId` for future multi-tenant support.
- Monetary values are stored as integer minor units.
- Timestamps are stored in UTC and displayed in the organization timezone.
- Important records support soft deletion via `deletedAt`.
- Sensitive mutations write audit-log entries.
- Authorization is enforced in server-side permission checks, not only in the UI.
- Intelligence stages request **connector roles** with distinct prompt templates — never identical fan-out to all models.
- OBSERVE and VERIFY prefer deterministic evidence over model prose.

## Layers

1. **UI** — `app/` routes and `components/` (including `/intelligence/*` cockpit)
2. **Validation** — Zod schemas in `validations/` and module folders
3. **Permissions** — `permissions/` role-to-capability mapping (`intelligence:*`)
4. **Services** — `modules/*/service.ts` business logic
5. **Cognitive pipeline** — `modules/intelligence` orchestrates domain engines + connectors
6. **Domain engines** — `crawl`, `seo`, `aeo`, `geo`, `visibility`, `knowledge`, `strategy`
7. **Connector fabric** — `modules/connectors` (OpenAI, Gemini, Anthropic, Perplexity, DeepSeek)
8. **Data** — Prisma multi-file schema in `prisma/schema/`
9. **Jobs** — `jobs/` queue abstraction (`run-intelligence-pipeline`, probes, crawl)
10. **Storage** — `lib/storage.ts` S3-compatible abstraction

## Next extraction path

Modules can later become services by extracting their service layer, schema slice, and jobs while keeping the same permission and audit contracts. The intelligence orchestrator is the natural boundary for a future visibility microservice.
