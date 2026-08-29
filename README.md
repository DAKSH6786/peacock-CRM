# peacock-CRM

All application code lives in **[`peacock-one/`](./peacock-one/)** — the single
project root for Peacock One (frontend, backend, AI connector plugins, SEO/AEO/GEO
engines, database migrations, scripts, docs, and tests).

```bash
cd peacock-one
cp .env.example .env
docker compose up --build
```

See [`peacock-one/README.md`](./peacock-one/README.md) for local development,
tests, and architecture.
