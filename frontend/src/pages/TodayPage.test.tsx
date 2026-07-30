import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { TodayPage } from "./TodayPage";

describe("TodayPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads the previous day when Previous day is clicked", async () => {
    vi.spyOn(tasksApi, "syncRoutineOccurrences").mockResolvedValue();
    const fetchTodayView = vi
      .spyOn(tasksApi, "fetchTodayView")
      .mockResolvedValueOnce({
        reference_date: "2026-07-21",
        items: [],
      })
      .mockResolvedValueOnce({
        reference_date: "2026-07-20",
        items: [],
      });

    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByText(/Jul 21/)).toBeVisible();
    });

    fireEvent.click(screen.getByRole("button", { name: "Previous day" }));

    await waitFor(() => {
      expect(fetchTodayView).toHaveBeenLastCalledWith("2026-07-20");
    });
  });
});
