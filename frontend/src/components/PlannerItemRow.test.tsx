import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { PlannerItemRow } from "./PlannerItemRow";

describe("PlannerItemRow", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders and fires complete callback for tasks", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(tasksApi, "completeTask").mockResolvedValue({
      id: "task-1",
      title: "Water the plants",
      notes: null,
      due_date: "2026-07-21",
      status: "completed",
      created_at: "2026-07-21T00:00:00Z",
      updated_at: "2026-07-21T00:00:00Z",
    });

    render(
      <PlannerItemRow
        item={{
          kind: "task",
          item_id: "task-1",
          title: "Water the plants",
          due_date: "2026-07-21",
          starts_at: null,
          ends_at: null,
          is_overdue: false,
        }}
        onChanged={onChanged}
      />,
    );

    expect(screen.getByText("Water the plants")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Complete" }));
    expect(onChanged).toHaveBeenCalled();
  });

  it("shows a visible error when a mutation fails", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(tasksApi, "completeTask").mockRejectedValue(
      new Error("Server unavailable"),
    );

    render(
      <PlannerItemRow
        item={{
          kind: "task",
          item_id: "task-1",
          title: "Water the plants",
          due_date: "2026-07-21",
          starts_at: null,
          ends_at: null,
          is_overdue: false,
        }}
        onChanged={onChanged}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Complete" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Server unavailable");
    expect(onChanged).not.toHaveBeenCalled();
  });
});
