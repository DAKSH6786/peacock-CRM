# Peacock Enterprise Reliability

Control plane for multi-provider Peacock runs. Cost and model diversity make reliability critical.

## Controls

| Control | Purpose |
| --- | --- |
| Idempotent jobs | Deduplicate work via `idempotency_key` |
| Retry policies | Backoff on transient timeouts / rate limits |
| Circuit breakers | Open on consecutive provider failures |
| Provider failover | Skip / fall back without aborting the report |
| Dead-letter queue | Park exhausted attempts for replay |
| Audit trails | Record reliability run writes |
| Rate limits | RPM envelope on provider calls |
| Cost limits | Hard µUSD ceiling for the run |
| Workflow recovery | Checkpoints for resume |
| Cancellation | Stop remaining calls on cancel signal |
| Partial results | Complete the report when some engines fail |

## Partial results policy

If one provider fails, Peacock should **not** necessarily fail the entire report.

Example:

> 4/5 AI engines successfully measured. DeepSeek unavailable during this run.

`report_status` becomes `completed_partial` when at least one engine succeeds.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/enterprise-reliability/catalog` | Controls, engines, retry/rate/cost defaults |
| `GET` | `/enterprise-reliability/preview` | Demo 4/5 + DeepSeek unavailable |
| `POST` | `/enterprise-reliability/runs` | Persist a reliability-aware run |
| `GET` | `/enterprise-reliability/runs/{id}` | Retrieve run + measurements |

## Tables

`enterprise_reliability_runs`, `er_provider_measurements`, `er_control_activations`, `er_dead_letter_events`, `er_circuit_states`, `er_workflow_checkpoints`

## Related

- Cost Intelligence pre-flight budgets (`docs/cost-intelligence.md`)
- Peacock mode hard envelopes (`docs/peacock-modes.md`)
- Job runtime ports (`packages/job_runtime`) — idempotency / cancel hooks
