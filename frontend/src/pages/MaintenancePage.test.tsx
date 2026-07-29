import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
  it("renders maintenance sections", async () => {
    render(<MaintenancePage />);
    expect(await screen.findByText("Overdue")).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "Maintenance history table" }),
    ).toBeInTheDocument();
  });
});
