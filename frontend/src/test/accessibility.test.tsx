import { cleanup, render } from "@testing-library/react";
import { axe } from "vitest-axe";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MaintenancePage } from "../pages/MaintenancePage";
import { SchedulePage } from "../pages/SchedulePage";
import { TodayPage } from "../pages/TodayPage";
import { WeekPage } from "../pages/WeekPage";

vi.mock("../lib/tasks", () => ({
  fetchTodayView: vi.fn().mockResolvedValue({ reference_date: "2026-07-21", items: [] }),
  fetchWeekView: vi.fn().mockResolvedValue({
    week_start: "2026-07-20",
    week_end: "2026-07-26",
    days: [],
    targets: [],
  }),
  syncRoutineOccurrences: vi.fn().mockResolvedValue(undefined),
  createWeeklyTarget: vi.fn(),
  deleteWeeklyTarget: vi.fn(),
  logWeeklyTargetProgress: vi.fn(),
  updateWeeklyTarget: vi.fn(),
  formatDisplayDate: (value: string) => value,
  listMaintenance: vi.fn().mockResolvedValue([]),
  fetchMaintenanceHistoryBoard: vi.fn().mockResolvedValue({
    rows: [],
    history_limit: 10,
  }),
  maintenanceNextActionLabel: () => "Needs scheduling",
  completeMaintenance: vi.fn(),
  archiveMaintenance: vi.fn(),
  restoreMaintenance: vi.fn(),
  listAppointments: vi.fn().mockResolvedValue([]),
  appointmentStatusLabel: () => "Scheduled",
  formatAppointmentSchedule: () => "Oct 4",
  archiveAppointment: vi.fn(),
  cancelAppointment: vi.fn(),
  completeAppointment: vi.fn(),
  reopenAppointment: vi.fn(),
  restoreAppointment: vi.fn(),
  deleteAppointment: vi.fn(),
}));

afterEach(() => {
  cleanup();
});

async function expectNoAccessibilityViolations(container: HTMLElement) {
  const results = await axe(container);
  expect(results.violations).toEqual([]);
}

describe("primary screen accessibility", () => {
  it("Today page has no detectable accessibility violations", async () => {
    const { container } = render(<TodayPage />);
    await expectNoAccessibilityViolations(container);
  });

  it("Week page has no detectable accessibility violations", async () => {
    const { container } = render(<WeekPage />);
    await expectNoAccessibilityViolations(container);
  });

  it("Schedule page has no detectable accessibility violations", async () => {
    const { container } = render(<SchedulePage />);
    await expectNoAccessibilityViolations(container);
  });

  it("Maintenance page has no detectable accessibility violations", async () => {
    const { container } = render(<MaintenancePage />);
    await expectNoAccessibilityViolations(container);
  });
});
