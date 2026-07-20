import { prisma } from "@/database";

/**
 * Reporting currency helpers.
 * We never silently sum across currencies — callers must convert via
 * exchange rates or restrict to the organization default currency.
 */
export async function organizationCurrency(
  organizationId: string,
): Promise<string> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    select: { currency: true },
  });
  return org?.currency ?? "INR";
}

export async function convertMinorUnits(input: {
  organizationId: string;
  amountMinor: number;
  fromCurrency: string;
  toCurrency: string;
  asOf: Date;
}): Promise<{ amountMinor: number; converted: boolean; rate: number }> {
  if (input.fromCurrency === input.toCurrency) {
    return { amountMinor: input.amountMinor, converted: false, rate: 1 };
  }

  const rate = await prisma.exchangeRate.findFirst({
    where: {
      organizationId: input.organizationId,
      baseCode: input.fromCurrency,
      quoteCode: input.toCurrency,
      effectiveAt: { lte: input.asOf },
    },
    orderBy: { effectiveAt: "desc" },
    select: { rate: true },
  });

  if (!rate) {
    throw new Error(
      `No exchange rate for ${input.fromCurrency}→${input.toCurrency} as of ${input.asOf.toISOString().slice(0, 10)}. Refusing to combine currencies.`,
    );
  }

  const numericRate = Number(rate.rate);
  return {
    amountMinor: Math.round(input.amountMinor * numericRate),
    converted: true,
    rate: numericRate,
  };
}

export function assertSingleCurrency(
  currencyCodes: string[],
  context: string,
): string {
  const unique = [...new Set(currencyCodes.filter(Boolean))];
  if (unique.length === 0) return "INR";
  if (unique.length > 1) {
    throw new Error(
      `${context}: mixed currencies (${unique.join(", ")}) without conversion.`,
    );
  }
  return unique[0]!;
}
