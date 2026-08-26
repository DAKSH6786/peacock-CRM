export type EntityNode = {
  name: string;
  entityType: string;
  description?: string;
};

export type EntityEdge = {
  from: string;
  to: string;
  relation: string;
  weight?: number;
};

export type KnowledgeGraph = {
  nodes: EntityNode[];
  edges: EntityEdge[];
};

export function buildKnowledgeGraph(input: {
  brand: string;
  domain: string;
  extracted?: Array<{ name: string; type: string }>;
}): KnowledgeGraph {
  const nodes: EntityNode[] = [
    {
      name: input.brand,
      entityType: "Organization",
      description: `Primary brand for ${input.domain}`,
    },
    {
      name: input.domain,
      entityType: "WebSite",
      description: "Primary web property",
    },
  ];

  for (const e of input.extracted ?? []) {
    if (
      !nodes.some(
        (n) =>
          n.name.toLowerCase() === e.name.toLowerCase() &&
          n.entityType === e.type,
      )
    ) {
      nodes.push({ name: e.name, entityType: e.type });
    }
  }

  const edges: EntityEdge[] = [
    { from: input.brand, to: input.domain, relation: "owns", weight: 1 },
  ];

  for (const node of nodes) {
    if (node.entityType !== "Organization" && node.name !== input.domain) {
      edges.push({
        from: input.brand,
        to: node.name,
        relation: "related_to",
        weight: 0.7,
      });
    }
  }

  return { nodes, edges };
}
