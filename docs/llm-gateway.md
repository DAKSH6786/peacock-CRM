# LLM Gateway

## Absolute rule

Provider-specific logic (SDKs, HTTP quirks, auth headers) lives **only** in:

`services/llm_gateway/adapters/*`

Domain engines call `LLMGateway.complete(LLMCompletionRequest)` with a **role** + **template_id**.

## Built-in controls

- Timeouts (`LLM_DEFAULT_TIMEOUT_SECONDS`)
- Retries with jitter (tenacity) for rate-limit/timeout classes
- Token usage + cost recording via `UsageTracker`
- Structured logging of completions
- Structured summaries only — **no private chain-of-thought storage**

## Providers

OpenAI, Anthropic, Gemini, Perplexity, DeepSeek adapters are scaffolded. Architecture stage uses `NullLLMProvider` so the stack runs without keys.
