import { formatMoney, formatPercent } from "@/lib/utils";

export function CurrencyDisplay({
  minorUnits,
  currency = "INR",
  locale = "en-IN",
}: {
  minorUnits: number;
  currency?: string;
  locale?: string;
}) {
  return (
    <span className="font-semibold tabular-nums">
      {formatMoney(minorUnits, currency, locale)}
    </span>
  );
}

export function PercentageDisplay({
  value,
  digits = 1,
}: {
  value: number;
  digits?: number;
}) {
  return (
    <span className="font-semibold tabular-nums">
      {formatPercent(value, digits)}
    </span>
  );
}
