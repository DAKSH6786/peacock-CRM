import type { PrismaClient } from "@prisma/client";

export async function seedIntelligence(
  prisma: PrismaClient,
  organizationId: string,
) {
  const property = await prisma.visibilityProperty.upsert({
    where: {
      organizationId_primaryDomain: {
        organizationId,
        primaryDomain: "digitalpeacock.com",
      },
    },
    update: {
      name: "Digital Peacock",
      rootUrl: "https://digitalpeacock.com",
      industry: "Marketing technology",
      metadata: { brand: "Digital Peacock" },
    },
    create: {
      organizationId,
      name: "Digital Peacock",
      primaryDomain: "digitalpeacock.com",
      rootUrl: "https://digitalpeacock.com",
      industry: "Marketing technology",
      metadata: { brand: "Digital Peacock" },
    },
  });

  await prisma.visibilityCompetitor.upsert({
    where: {
      propertyId_domain: {
        propertyId: property.id,
        domain: "competitor-seo.example",
      },
    },
    update: { name: "Competitor SEO Suite" },
    create: {
      propertyId: property.id,
      name: "Competitor SEO Suite",
      domain: "competitor-seo.example",
      rootUrl: "https://competitor-seo.example",
    },
  });

  const keywords = [
    "AI visibility platform",
    "answer engine optimization",
    "generative engine optimization",
  ];
  for (const phrase of keywords) {
    await prisma.keywordTarget.upsert({
      where: {
        propertyId_phrase_locale: {
          propertyId: property.id,
          phrase,
          locale: "en-US",
        },
      },
      update: {},
      create: {
        propertyId: property.id,
        phrase,
        locale: "en-US",
        intent: "commercial",
        priority: "HIGH",
      },
    });
  }

  return property;
}
