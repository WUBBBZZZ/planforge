const WEEKDAY_BY_NAME: Record<string, number> = {
  monday: 0,
  tuesday: 1,
  wednesday: 2,
  thursday: 3,
  friday: 4,
  saturday: 5,
  sunday: 6,
};

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function parseIsoDate(isoDate: string): {
  year: number;
  month: number;
  day: number;
} {
  const [year, month, day] = isoDate.split("-").map(Number);
  return { year, month, day };
}

export function toIsoDate(year: number, month: number, day: number): string {
  return `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
}

export function addDays(isoDate: string, days: number): string {
  const { year, month, day } = parseIsoDate(isoDate);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + days);
  return toIsoDate(date.getFullYear(), date.getMonth() + 1, date.getDate());
}

export function addMonths(monthKey: string, months: number): string {
  const [year, month] = monthKey.split("-").map(Number);
  const date = new Date(year, month - 1, 1);
  date.setMonth(date.getMonth() + months);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, "0")}`;
}

export function formatMonthYear(monthKey: string): string {
  const [year, month] = monthKey.split("-").map(Number);
  const date = new Date(year, month - 1, 1);
  const currentYear = new Date().getFullYear();
  return date.toLocaleDateString(undefined, {
    month: "long",
    ...(year !== currentYear ? { year: "numeric" } : {}),
  });
}

export function weekdayLabels(weekStartDay = "monday"): string[] {
  const start = WEEKDAY_BY_NAME[weekStartDay] ?? 0;
  return Array.from({ length: 7 }, (_, index) => WEEKDAY_LABELS[(start + index) % 7]);
}

export function leadingPaddingDays(
  monthStartIso: string,
  weekStartDay = "monday",
): number {
  const { year, month, day } = parseIsoDate(monthStartIso);
  const firstWeekday = new Date(year, month - 1, day).getDay();
  const mondayBased = firstWeekday === 0 ? 6 : firstWeekday - 1;
  const start = WEEKDAY_BY_NAME[weekStartDay] ?? 0;
  return (mondayBased - start + 7) % 7;
}

export function getSearchParam(key: string): string | null {
  return new URLSearchParams(window.location.search).get(key);
}

export function setSearchParam(key: string, value: string | null): void {
  const params = new URLSearchParams(window.location.search);
  if (value === null) {
    params.delete(key);
  } else {
    params.set(key, value);
  }
  const query = params.toString();
  const nextUrl = query
    ? `${window.location.pathname}?${query}`
    : window.location.pathname;
  window.history.replaceState(null, "", nextUrl);
}

export function todayIsoLocal(): string {
  const now = new Date();
  return toIsoDate(now.getFullYear(), now.getMonth() + 1, now.getDate());
}
