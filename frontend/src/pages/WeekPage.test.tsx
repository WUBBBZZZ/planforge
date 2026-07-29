import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { WeekPage } from "./WeekPage";

describe("WeekPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows loading then empty state", async () => {
    vi.spyOn(tasksApi, "syncRoutineOccurrences").mockResolvedValue();
    vi.spyOn(tasksApi, "fetchWeekView").mockResolvedValue({
      week_start: "2026-07-20",
      week_end: "2026-07-26",
      days: Array.from({ length: 7 }, (_, index) => ({
        date: `2026-07-${20 + index}`,
        items: [],
      })),
      targets: [],
    });

    render(<WeekPage />);

    expect(screen.getByText("Loading week view")).toBeVisible();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "No items this week" })).toBeVisible();
    });
  });

  it("loads the next week when Next is clicked", async () => {
    vi.spyOn(tasksApi, "syncRoutineOccurrences").mockResolvedValue();
    const fetchWeekView = vi
      .spyOn(tasksApi, "fetchWeekView")
      .mockResolvedValueOnce({
        week_start: "2026-07-20",
        week_end: "2026-07-26",
        days: Array.from({ length: 7 }, (_, index) => ({
          date: `2026-07-${20 + index}`,
          items: [],
        })),
        targets: [],
      })
      .mockResolvedValueOnce({
        week_start: "2026-07-27",
        week_end: "2026-08-02",
        days: Array.from({ length: 7 }, (_, index) => ({
          date: `2026-07-${27 + index}`,
          items: [],
        })),
        targets: [],
      });

    render(<WeekPage />);

    await waitFor(() => {
      expect(screen.getByText(/Jul 20/)).toBeVisible();
      expect(screen.getByText(/Jul 26/)).toBeVisible();
    });

    fireEvent.click(screen.getByRole("button", { name: "Next week" }));

    await waitFor(() => {
      expect(fetchWeekView).toHaveBeenLastCalledWith("2026-07-27");
    });
  });
});
