# Cursor Execution Rule

For each Peacock One subsystem (or stacked PR):

1. **Inspect** existing implementation.
2. Produce a brief **implementation plan**.
3. Identify **schema changes**.
4. Implement **backend domain logic**.
5. Implement **API endpoints**.
6. Implement **asynchronous processing** where required (jobs / Celery).
7. Implement **frontend**.
8. Add **tests**.
9. Run **existing tests**.
10. Run **new tests**.
11. Run **lint**.
12. Run **typecheck**.
13. **Fix** failures.
14. Update **documentation**.
15. State exactly **what is functional**.
16. State **what requires external credentials**.
17. **Do not** claim unfinished or mocked functionality works.

## Hard gate

Do **not** move to the next major subsystem until the current subsystem **builds successfully**.

## Honesty

- Demo / preview engines with optional DB persistence are **functional for the demo contract** (catalog, preview, persist, retrieve).
- They are **not** live production integrations unless wired to real providers, crawlers, or job runners.
- Frontend demo fallbacks must be labeled when the API is unreachable.
