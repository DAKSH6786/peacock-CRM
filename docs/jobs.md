# Job runtime

## Port

`packages/job_runtime.JobRunner` defines:

- `enqueue(JobSubmission) -> JobHandle`
- `get_status(job_id) -> JobHandle`
- `cancel(job_id) -> JobHandle`

## Backends

| `JOB_BACKEND` | Implementation | Use |
| --- | --- | --- |
| `celery` | `CeleryJobRunner` | Default local/prod path |
| `memory` | `InMemoryJobRunner` | Unit tests |
| `temporal` | `TemporalJobRunner` stub | Future swap |

Business services and API routes depend on the **port**, not Celery APIs. Replacing Celery with Temporal means implementing `TemporalJobRunner` and flipping config.

## Status tracking

Every enqueue persists a `background_jobs` row with organisation scope, status, payload, result, and error.
