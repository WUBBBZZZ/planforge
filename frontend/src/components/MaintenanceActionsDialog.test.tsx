import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MaintenanceActionsDialog } from "./MaintenanceActionsDialog";

vi.mock("../lib/tasks", () => ({
  getMaintenance: vi.fn().mockResolvedValue({
    id: "m1",
    title: "Dentist",
    category: null,
    notes: null,
    interval_unit: "months",
    interval_value: 6,
    last_completed_date: "2026-07-27",
    next_due_date: "2027-01-27",
    next_action_status: "needs_scheduling",
    linked_appointment_id: null,
    scheduling_reminder_date: null,
    reminder_offset_days: null,
    lead_time_days: 30,
    status: "active",
    linked_appointment: null,
    completions: [],
  }),
  listAppointments: vi.fn().mockResolvedValue([]),
  formatDisplayDate: (value: string) => value,
  formatAppointmentSchedule: () => "Oct 4",
}));

describe("MaintenanceActionsDialog", () => {
  it("renders action selector and history state", async () => {
    render(
      <MaintenanceActionsDialog
        open
        item={{
          id: "m1",
          title: "Dentist",
          category: null,
          notes: null,
          interval_unit: "months",
          interval_value: 6,
          last_completed_date: null,
          next_due_date: null,
          next_action_status: "no_next_date",
          linked_appointment_id: null,
          scheduling_reminder_date: null,
          reminder_offset_days: null,
          lead_time_days: 30,
          status: "active",
        }}
        onClose={vi.fn()}
        onSaved={vi.fn()}
      />,
    );

    expect(await screen.findByText("No completion history yet.")).toBeInTheDocument();
    expect(screen.getByLabelText("Action")).toBeInTheDocument();
  });
});
