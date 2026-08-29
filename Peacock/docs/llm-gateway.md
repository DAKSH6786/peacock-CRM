# LLM Gateway

## Absolute rule

Provider-specific logic (SDKs, HTTP quirks, auth headers) lives **only** in:

`plugins/llm_gateway/adapters/*` (also exposed as `plugins/openai`, `plugins/gemini`, `plugins/claude`, `plugins/perplexity`, `plugins/deepseek`)

Domain engines call `LLMGateway.complete(LLMCompletionRequest)` with a **role** + **template_id**.

Prefer **dynamic capability routing** (`CapabilityRouter` → set `request.provider` /
`request.model`) over static role→provider maps. Soft static `role_routing` is a
fallback only — never a permanent Claude=critic / Perplexity=research / GPT=strategy lock.

See [`capability-profiles.md`](./capability-profiles.md).

## Built-in controls

- Timeouts (`LLM_DEFAULT_TIMEOUT_SECONDS`)
- Retries with jitter (tenacity) for rate-limit/timeout classes
- Token usage + cost recording via `UsageTracker`
- Structured logging of completions
- Structured summaries only — **no private chain-of-thought storage**
- Optional dynamic provider override on each request

## Providers

OpenAI, Anthropic, Gemini, Perplexity, DeepSeek adapters are scaffolded. Architecture stage uses `NullLLMProvider` so the stack runs without keys.
