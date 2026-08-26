export type StrategyWeek = {
  week: number;
  theme: string;
  outcomes: string[];
  workItems: string[];
};

export type NinetyDayPlan = {
  title: string;
  horizonDays: 90;
  summary: string;
  weeks: StrategyWeek[];
};

export function buildNinetyDayPlan(input: {
  brand: string;
  priorities: string[];
  technicalCodes: string[];
  aeoCodes: string[];
  geoCodes: string[];
}): NinetyDayPlan {
  const weeks: StrategyWeek[] = [
    {
      week: 1,
      theme: "Observe & baseline",
      outcomes: ["Full crawl baseline", "Visibility probe baseline"],
      workItems: ["Run intelligence loop", "Inventory competitors"],
    },
    {
      week: 2,
      theme: "Technical foundations",
      outcomes: ["Critical technical SEO cleared"],
      workItems: input.technicalCodes.slice(0, 4).map((c) => `Fix ${c}`),
    },
    {
      week: 3,
      theme: "Entity clarity",
      outcomes: ["Organization entity consistent across site"],
      workItems: input.geoCodes.map((c) => `Address ${c}`),
    },
    {
      week: 4,
      theme: "Answer surfaces",
      outcomes: ["FAQ/HowTo extractability improved"],
      workItems: input.aeoCodes.map((c) => `Ship ${c} remediation`),
    },
    {
      week: 5,
      theme: "Content clusters",
      outcomes: ["Priority topic cluster live"],
      workItems: ["Writer briefs for top 3 intents", "Publish cluster hub"],
    },
    {
      week: 6,
      theme: "Citation & authority",
      outcomes: ["Citation targets engaged"],
      workItems: ["Outreach list", "Digital PR angles"],
    },
    {
      week: 7,
      theme: "GEO reinforcement",
      outcomes: ["Quotable facts & stats pages"],
      workItems: ["Fact sheets", "Source pages"],
    },
    {
      week: 8,
      theme: "AEO expansion",
      outcomes: ["Expanded Q&A coverage"],
      workItems: ["Additional FAQ hubs", "Schema QA"],
    },
    {
      week: 9,
      theme: "Competitor gap close",
      outcomes: ["Close top competitor content gaps"],
      workItems: input.priorities.slice(0, 3).map((p) => `Execute: ${p}`),
    },
    {
      week: 10,
      theme: "Measurement cadence",
      outcomes: ["Weekly AI visibility scorecard"],
      workItems: ["Automate probes", "Outcome dashboards"],
    },
    {
      week: 11,
      theme: "Optimize & learn",
      outcomes: ["Weights updated from outcomes"],
      workItems: ["Review recommendation performance", "Retire weak plays"],
    },
    {
      week: 12,
      theme: "Next-quarter brief",
      outcomes: ["Board-ready visibility report"],
      workItems: ["Executive summary", "Quarter+1 backlog"],
    },
  ];

  return {
    title: `90-day generative visibility plan — ${input.brand}`,
    horizonDays: 90,
    summary: `Prioritize ${input.priorities.slice(0, 3).join(", ") || "technical + AEO + entity"} with continuous measurement.`,
    weeks,
  };
}
