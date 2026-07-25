import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { WeekPage } from "./WeekPage";

describe("WeekPage", () => {
  it("shows loading then empty state", async () => {
    vi.spyOn(tasksApi, "fetchWeekView").mockResolvedValue({
      week_start: "2026-07-20",
      week_end: "2026-07-26",
      days: Array.from({ length: 8 }, (_, index) => ({
        date: index < 7 ? `2026-07-${20 + index}` : null,
        tasks: [],
      })),
    });

    render(<WeekPage />);

    expect(screen.getByText("Loading week view")).toBeVisible();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "No tasks this week" })).toBeVisible();
    });
  });
});
