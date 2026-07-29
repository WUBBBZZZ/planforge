import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SchedulePage } from "./SchedulePage";

vi.mock("../lib/tasks", () => ({
  listAppointments: vi.fn().mockResolvedValue([
    {
      id: "apt-1",
      title: "Doctor",
      notes: null,
      location: "Clinic",
      category: "health",
      reminder_minutes: null,
      maintenance_definition_id: null,
      is_all_day: false,
      start_date: "2026-07-21",
      end_date: "2026-07-21",
      starts_at: "2026-07-21T16:00:00+00:00",
      ends_at: "2026-07-21T17:00:00+00:00",
      status: "scheduled",
      created_at: "2026-07-21T00:00:00+00:00",
      updated_at: "2026-07-21T00:00:00+00:00",
    },
  ]),
  appointmentStatusLabel: (status: string) => status,
  formatAppointmentSchedule: () => "Jul 21",
  completeAppointment: vi.fn(),
  cancelAppointment: vi.fn(),
  archiveAppointment: vi.fn(),
  deleteAppointment: vi.fn(),
  reopenAppointment: vi.fn(),
  restoreAppointment: vi.fn(),
}));

describe("SchedulePage", () => {
  it("renders upcoming appointments", async () => {
    render(<SchedulePage />);
    expect(await screen.findByText("Doctor")).toBeInTheDocument();
    expect(screen.getByText("Clinic")).toBeInTheDocument();
  });
});
