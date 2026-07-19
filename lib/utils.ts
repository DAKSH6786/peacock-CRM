import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format integer minor units (cents) as a currency string. */
export function formatMoney(
  minorUnits: number,
  currency = "USD",
  locale = "en-US",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(minorUnits / 100);
}

/** Convert a major-unit decimal string/number to integer minor units. */
export function toMinorUnits(amount: number): number {
  return Math.round(amount * 100);
}
