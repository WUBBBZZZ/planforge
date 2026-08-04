import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { MonthPage } from "./MonthPage";

describe("MonthPage", () => {
  it("renders the month grid", async () => {
    vi.spyOn(tasksApi, "syncRoutineOccurrences").mockResolvedValue();
    vi.spyOn(tasksApi, "fetchMonthView").mockResolvedValue({
      month: "2026-07",
      month_start: "2026-07-01",
      month_end: "2026-07-31",
      week_start_day: "monday",
      days: Array.from({ length: 31 }, (_, index) => ({
        date: `2026-07-${(index + 1).toString().padStart(2, "0")}`,
        items: [],
      })),
    });

    render(<MonthPage />);

    expect(screen.getByText("Loading month view")).toBeVisible();

    await waitFor(() => {
      expect(screen.getByRole("table", { name: "July" })).toBeVisible();
      expect(screen.getByRole("columnheader", { name: "Mon" })).toBeVisible();
      expect(screen.getByRole("columnheader", { name: "Sun" })).toBeVisible();
    });
  });
});
