# Peacock One — Product Philosophy

Peacock One is an enterprise-grade **SEO + AEO + GEO Search & Generative Visibility Intelligence Platform**.

It must **not** behave like a thin wrapper around LLM APIs.

## Cognitive loop

Every material workflow follows:

```text
OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN
```

| Stage       | Responsibility                                                                                                   | LLM role                                              |
| ----------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **OBSERVE** | Crawl sites, extract technical SEO signals, fetch keyword/backlink/competitor evidence, probe AI answer surfaces | Minimal — structured extractors preferred             |
| **THINK**   | Multi-layer specialist reasoning over observed evidence                                                          | Differentiated prompts & model roles                  |
| **VERIFY**  | Cross-check claims against evidence, consensus, and deterministic rules                                          | Adversarial / fact-check roles only                   |
| **DECIDE**  | Score, prioritize, and policy-gate recommendations                                                               | Optional synthesis; decisions are rule + score driven |
| **EXECUTE** | Produce content briefs, writer packs, technical fix queues, 90-day strategies                                    | Generation grounded in decided actions                |
| **MEASURE** | Track rankings, AI citations, visibility share, outcome KPIs                                                     | Probe prompts differ from think prompts               |
| **LEARN**   | Update recommendation weights from measured outcomes                                                             | Offline / batch model refresh                         |

## What Peacock One combines

- Website crawling
- Technical SEO
- Content analysis
- GEO analysis (generative engine optimization)
- AEO analysis (answer engine optimization)
- AI visibility measurement
- Cross-LLM research
- Competitor intelligence
- Keyword intelligence
- Backlink intelligence
- Entity analysis
- Knowledge graphs
- Content recommendations
- Writer recommendations
- 90-day strategy generation
- Continuous monitoring
- Outcome tracking
- Self-learning recommendation models

## AI connectors (underneath, not the product)

Connectors exist for:

- OpenAI / ChatGPT
- Google Gemini
- Anthropic Claude
- Perplexity
- DeepSeek

**Hard rule:** never send the same prompt to every model and average the answers.

Each provider is assigned **specialist roles** in the reasoning stack (see `docs/intelligence-architecture.md`). Observation evidence always anchors THINK and VERIFY.

## Product boundary

The internal business OS modules (CRM, delivery, finance, HR) remain available as the operating layer for Digital Peacock.

The **differentiating product surface** of Peacock One is generative search & visibility intelligence — the cognitive loop above.
