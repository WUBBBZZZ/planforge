import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MaintenancePage } from "./MaintenancePage";

vi.mock("../lib/tasks", () => ({
  listMaintenance: vi.fn().mockResolvedValue([]),
  fetchMaintenanceHistoryBoard: vi.fn().mockResolvedValue({
    rows: [],
    history_limit: 10,
  }),
  maintenanceNextActionLabel: () => "Needs scheduling",
  completeMaintenance: vi.fn(),
  archiveMaintenance: vi.fn(),
  restoreMaintenance: vi.fn(),
  formatDisplayDate: (value: string) => value,
}));

describe("MaintenancePage", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows items by default and history after switching tabs", async () => {
    const user = userEvent.setup();
    render(<MaintenancePage />);

    expect(await screen.findByText("Overdue")).toBeInTheDocument();
    expect(
      screen.queryByRole("table", { name: "Maintenance history table" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "History" }));

    expect(
      await screen.findByRole("table", { name: "Maintenance history table" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Overdue")).not.toBeInTheDocument();
  });
});
