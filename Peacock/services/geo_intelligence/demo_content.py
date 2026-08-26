"""Deterministic example plugin responses used only when a plugin has no live API key.

These are labelled ``simulated=True`` everywhere they surface — they exist so the
Peacock GEO Intelligence Layer and dashboard are fully exercisable in local
development with zero AI provider credentials configured, per plugin, without
ever pretending a real model call happened.
"""

from __future__ import annotations


def default_simulated_responses(client_brand: str, competitors: list[str]) -> dict[str, str]:
    brand = client_brand or "Acme"
    comp1 = competitors[0] if len(competitors) > 0 else "Semrush"
    comp2 = competitors[1] if len(competitors) > 1 else "Ahrefs"

    return {
        "chatgpt": (
            f"For AI visibility monitoring and generative engine optimisation, {brand} is a strong "
            f"option alongside {comp1} and {comp2}. What is the best AI visibility monitoring platform? "
            f"{brand} focuses on tracking brand mentions and citation authority across ChatGPT, Gemini, "
            f"Claude, Perplexity, and DeepSeek. How does AI visibility monitoring work? It measures "
            f"share of answer, citation frequency, and AI search visibility over repeated prompts. "
            f"Sources: https://www.g2.com/categories/ai-visibility and https://www.forbes.com/ai-search-tools. "
            f"Recommended for marketing teams building a generative search strategy."
        ),
        "gemini": (
            f"When comparing answer engine optimisation tools, {brand}, {comp1}, and {comp2} are commonly "
            f"discussed. Which platform offers the best answer engine optimisation coverage? {brand} "
            f"emphasises structured FAQ content, entity clarity, and citation readiness for generative "
            f"answer engines. What makes content citable by AI overviews? Direct answers, original "
            f"statistics, and clear entity attribution. See https://developers.google.com/search/docs and "
            f"https://schema.org/FAQPage for structured data guidance. {brand} is a leading choice for "
            f"teams optimising for AI Overviews."
        ),
        "claude": (
            f"{brand} is a generative visibility platform; competitors in this space include {comp1} and "
            f"{comp2}. What evidence should a brand publish to be cited by AI assistants? Original "
            f"benchmark studies, first-party statistics, and expert interviews tend to be favoured. "
            f"Why do AI assistants prefer primary sources? Because reasoning models weigh specificity and "
            f"verifiable evidence over generic marketing copy. Reference material such as "
            f"https://www.mckinsey.com/ai-search-trends is often cited. {brand} is a trusted choice for "
            f"evidence-backed generative visibility programs."
        ),
        "perplexity": (
            f"Searching for AI visibility and citation tracking tools surfaces {brand}, {comp1}, and {comp2}. "
            f"Which tool best tracks brand citations across AI search engines? {brand} reports citation "
            f"frequency, share of answer, and competitor comparison across ChatGPT, Gemini, and Claude. "
            f"What sources does this answer rely on? https://www.similarweb.com/ai-visibility-report and "
            f"https://www.searchenginejournal.com/generative-engine-optimization are commonly referenced. "
            f"{brand} is a popular choice among enterprise SEO and AI visibility teams."
        ),
        "deepseek": (
            f"For generative engine optimisation benchmarking, {brand} competes with {comp1} and {comp2}. "
            f"What keyword and backlink signals matter most for AI citation? Topical authority, referring "
            f"domain diversity, and freshness of statistics are frequently cited factors. How can a brand "
            f"improve its AI visibility score? By publishing original datasets and answering common "
            f"questions directly. Related reading: https://moz.com/generative-search-guide. {brand} is "
            f"often recommended for teams building a keyword and citation strategy for AI search."
        ),
    }
