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

  it("reopens completed tasks", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(tasksApi, "reopenTask").mockResolvedValue({
      id: "task-1",
      title: "Water the plants",
      notes: null,
      due_date: "2026-07-21",
      status: "pending",
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
          is_completed: true,
        }}
        onChanged={onChanged}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Reopen" }));
    expect(onChanged).toHaveBeenCalled();
  });

  it("moves pending tasks to backlog after confirmation", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.spyOn(tasksApi, "moveTaskToBacklog").mockResolvedValue({
      task: {
        id: "task-1",
        title: "Water the plants",
        notes: null,
        due_date: null,
        status: "moved_to_backlog",
        created_at: "2026-07-21T00:00:00Z",
        updated_at: "2026-07-21T00:00:00Z",
      },
      backlog_item: {
        id: "backlog-1",
        title: "Water the plants",
        notes: null,
        status: "active",
        promoted_entity_type: null,
        promoted_entity_id: null,
        source_entity_type: "task",
        source_entity_id: "task-1",
      },
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

    await user.click(screen.getByRole("button", { name: "Move to backlog" }));
    expect(onChanged).toHaveBeenCalled();
  });

  it("opens the edit dialog for pending tasks", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);

    render(
      <PlannerItemRow
        item={{
          kind: "task",
          item_id: "task-1",
          title: "Water the plants",
          notes: "Notes",
          due_date: "2026-07-21",
          starts_at: null,
          ends_at: null,
          is_overdue: false,
        }}
        onChanged={onChanged}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("dialog", { name: "Edit task" })).toBeVisible();
    expect(screen.getByDisplayValue("Water the plants")).toBeVisible();
  });

  it("renders read-only week preview items without actions", () => {
    render(
      <PlannerItemRow
        item={{
          kind: "occurrence",
          item_id: "occ-1",
          title: "Exercise",
          due_date: "2026-07-21",
          starts_at: null,
          ends_at: null,
          is_overdue: false,
        }}
        onChanged={vi.fn().mockResolvedValue(undefined)}
        readOnly
      />,
    );

    expect(screen.getByText("Exercise")).toBeVisible();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
