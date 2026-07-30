import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { formatMonthYear } from "./dates";
import { formatDisplayDate, maintenanceNextActionLabel, maintenanceScheduleByDate } from "./tasks";

describe("formatDisplayDate", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 30));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("omits the year for dates in the current year", () => {
    expect(formatDisplayDate("2026-08-15")).not.toContain("2026");
  });

  it("includes the year for dates outside the current year", () => {
    expect(formatDisplayDate("2027-01-15")).toContain("2027");
    expect(formatDisplayDate("2025-12-01")).toContain("2025");
  });
});

describe("formatMonthYear", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 30));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("omits the year for the current calendar year", () => {
    expect(formatMonthYear("2026-08")).toBe("August");
  });

  it("includes the year for other years", () => {
    expect(formatMonthYear("2027-01")).toContain("2027");
  });
});

describe("maintenanceScheduleByDate", () => {
  it("subtracts lead time from the due date", () => {
    expect(
      maintenanceScheduleByDate({
        next_due_date: "2026-09-30",
        lead_time_days: 30,
      } as Parameters<typeof maintenanceScheduleByDate>[0]),
    ).toBe("2026-08-31");
  });

  it("labels schedule by using the lead window start", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 30));
    const label = maintenanceNextActionLabel({
      next_action_status: "needs_scheduling",
      next_due_date: "2026-09-30",
      lead_time_days: 30,
    } as Parameters<typeof maintenanceNextActionLabel>[0]);
    expect(label).toContain("Schedule by");
    expect(label).toContain("Aug");
    vi.useRealTimers();
  });
});
