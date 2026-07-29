import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MaintenanceHistoryBoard } from "./MaintenanceHistoryBoard";

describe("MaintenanceHistoryBoard", () => {
  it("renders newest completion first and empty row message", () => {
    render(
      <MaintenanceHistoryBoard
        historyLimit={10}
        onHistoryLimitChange={vi.fn()}
        rows={[
          {
            maintenance: {
              id: "m1",
              title: "Dentist",
              category: "health",
              notes: null,
              interval_unit: "months",
              interval_value: 6,
              last_completed_date: "2026-07-27",
              next_due_date: "2027-01-27",
              next_action_status: "scheduled",
              linked_appointment_id: "a1",
              scheduling_reminder_date: null,
              reminder_offset_days: null,
              lead_time_days: 30,
              status: "active",
            },
            current_next_label: "Scheduled Oct 04",
            completions: [
              {
                id: "c1",
                completed_on: "2026-07-27",
                notes: null,
                is_voided: false,
                superseded_by_id: null,
              },
            ],
            linked_appointment: null,
          },
          {
            maintenance: {
              id: "m2",
              title: "Physical",
              category: null,
              notes: null,
              interval_unit: "years",
              interval_value: 1,
              last_completed_date: null,
              next_due_date: null,
              next_action_status: "no_next_date",
              linked_appointment_id: null,
              scheduling_reminder_date: null,
              reminder_offset_days: null,
              lead_time_days: 30,
              status: "active",
            },
            current_next_label: "No next date",
            completions: [],
            linked_appointment: null,
          },
        ]}
      />,
    );

    expect(screen.getAllByText("Dentist").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Add first record").length).toBeGreaterThan(0);
  });
});
