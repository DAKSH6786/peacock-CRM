# Peacock Content Lab

Upgrade of Content Intelligence — substantially beyond keyword recommendations.

## Opportunity dimensions

For every proposed piece of content, evaluate (0–100):

| Dimension | Role |
| --- | --- |
| SEO Opportunity | Classic search demand / rankability |
| AEO Opportunity | Answer-engine eligibility |
| GEO Opportunity | Generative-engine visibility |
| AI Citation Opportunity | Likelihood of being cited in AI answers |
| Business Value | Commercial upside |
| Audience Relevance | Fit to ICP / intent |
| Competitor Gap | Whitespace vs rivals |
| Information Gain | Adds net-new information |
| Originality Opportunity | Room for unique creative/IP |
| Topical Authority Impact | Cluster authority lift |
| Conversion Potential | Path to pipeline/revenue |
| Backlink Potential | Link-earning likelihood |
| Entity Impact | Brand/entity graph strengthening |
| Effort | Cost to produce (higher = harder) |
| Time Sensitivity | Urgency / decay risk |

## Information Gain Score

Estimates whether proposed content **adds information beyond what already exists**.

**Penalises:** generic duplication, near-identical competitor coverage, common definitions, repeated statistics, commodity advice.

**Rewards:** original data, original experiment, new comparison, expert opinion, first-party insight, unique framework, new synthesis, fresh statistics, novel example.

## Content Moat Score

Estimates how difficult the content would be for competitors to replicate.

| Format | Moat |
| --- | ---: |
| Generic listicle | 18/100 |
| Expert interview | 51/100 |
| Original dataset | 86/100 |
| Proprietary benchmark study | 94/100 |

## Generative Citability Score

Peacock's **proprietary estimate** of whether a page is likely to offer useful quotable/retrievable information.

Considers: specificity, evidence, direct answers, original information, entity clarity, source attribution, freshness, structured information, tables, definitions, comparisons.

**Not** presented as a guaranteed third-party ranking factor. Always labelled as Peacock's proprietary estimate.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/content-lab/catalog` | Dimensions, moat priors, disclaimer |
| `POST` | `/content-lab/analyses` | Evaluate proposals |
| `GET` | `/content-lab/analyses/{id}` | Retrieve report |
