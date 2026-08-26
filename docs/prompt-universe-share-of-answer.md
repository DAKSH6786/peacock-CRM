# Prompt Universe & Share of Answer

## Prompt Universe

Competitors usually track a manually configured prompt set (25 / 50 / 100).

Peacock One builds a **Prompt Universe** — the complete intent landscape —
from products, services, keywords, Search Console, competitor rankings,
forums, SERPs, People Also Ask, personas, funnel stages, locations, industry
concepts, AI query patterns, and taxonomy.

Every prompt carries:

`topic` · `subtopic` · `intent` · `persona` · `funnel_stage` · `location` ·
`product` · `problem` · `commercial_value` · `brand_relevance` · `prompt_type`

Prompt types: Discovery, Recommendation, Comparison, Problem Solving,
Purchase, Research, Validation, Alternative, Pricing, Trust, Risk, Technical,
Educational, Transactional.

Synthetic personas (analytical, not fake identities): CFO, CMO, Student,
Enterprise buyer, Technical evaluator, HNWI, Small business owner, Developer,
Parent, Healthcare professional.

Both **simple** (`best CRM`) and **contextual** persona shortlist prompts are
tracked under the same family.

- Module: `modules/prompt-universe`
- UI: `/intelligence/prompt-universe`
- API: `GET|POST /api/intelligence/prompt-universe`

## Share of Answer

Traditional tools use Share of Voice. Peacock additionally measures
**Share of Answer** — how much of a generative answer is controlled by or
favourable to each brand/entity.

Indicators:

mention · position · recommendation strength · answer space ·
citation ownership · semantic prominence · positive / negative / neutral
claims · comparison outcome

**Token count alone is rejected** as methodology. Token span is diagnostic
only (`tokenOnlyShare`, `tokenVsInfluenceGap`).

Example cluster **Enterprise CRM**: Brand A 34% · Brand B 28% · Client 11%.

- Module: `modules/share-of-answer`
- UI: `/intelligence/share-of-answer`
- API: `GET|POST /api/intelligence/share-of-answer`
