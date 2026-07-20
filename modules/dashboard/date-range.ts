export type DashboardDateRange = {
  from: Date;
  to: Date;
  label: string;
};

function startOfDay(date: Date): Date {
  const d = new Date(date);
  d.setUTCHours(0, 0, 0, 0);
  return d;
}

function endOfDay(date: Date): Date {
  const d = new Date(date);
  d.setUTCHours(23, 59, 59, 999);
  return d;
}

export function parseDashboardRange(
  fromParam?: string | null,
  toParam?: string | null,
): DashboardDateRange {
  const now = new Date();
  const defaultFrom = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1),
  );
  const defaultTo = endOfDay(now);

  const from = fromParam ? startOfDay(new Date(fromParam)) : defaultFrom;
  const to = toParam ? endOfDay(new Date(toParam)) : defaultTo;

  if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime()) || from > to) {
    return {
      from: defaultFrom,
      to: defaultTo,
      label: "Current month",
    };
  }

  return {
    from,
    to,
    label: `${from.toISOString().slice(0, 10)} → ${to.toISOString().slice(0, 10)}`,
  };
}

export function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}
