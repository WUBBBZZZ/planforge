import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppointmentEditDialog } from "./AppointmentEditDialog";

vi.mock("../lib/tasks", () => ({
  createAppointment: vi.fn().mockResolvedValue({ id: "apt-1" }),
  updateAppointment: vi.fn().mockResolvedValue({ id: "apt-1" }),
  rescheduleAppointment: vi.fn().mockResolvedValue({ id: "apt-1" }),
}));

describe("AppointmentEditDialog", () => {
  it("submits an all-day appointment", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const onClose = vi.fn();
    const { createAppointment } = await import("../lib/tasks");

    render(
      <AppointmentEditDialog
        open
        appointment={null}
        onClose={onClose}
        onSaved={onSaved}
      />,
    );

    await user.type(screen.getByLabelText("Title"), "Vacation");
    await user.click(screen.getByRole("checkbox"));
    fireEvent.change(screen.getByLabelText("Start date"), {
      target: { value: "2026-07-21" },
    });
    fireEvent.change(screen.getByLabelText("End date"), {
      target: { value: "2026-07-25" },
    });
    await user.click(screen.getByRole("button", { name: "Create appointment" }));

    expect(createAppointment).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Vacation",
        is_all_day: true,
        start_date: "2026-07-21",
        end_date: "2026-07-25",
      }),
    );
    expect(onSaved).toHaveBeenCalled();
  });
});
