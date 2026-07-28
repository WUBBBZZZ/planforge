import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { TaskEditDialog } from "./TaskEditDialog";

describe("TaskEditDialog", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("submits updated task fields", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const onClose = vi.fn();
    vi.spyOn(tasksApi, "updateTask").mockResolvedValue({
      id: "task-1",
      title: "Updated title",
      notes: "Updated notes",
      due_date: "2026-07-22",
      status: "pending",
      created_at: "2026-07-21T00:00:00Z",
      updated_at: "2026-07-21T00:00:00Z",
    });

    render(
      <TaskEditDialog
        open
        task={{
          id: "task-1",
          title: "Original title",
          notes: "Original notes",
          due_date: "2026-07-21",
        }}
        onClose={onClose}
        onSaved={onSaved}
      />,
    );

    const dialog = screen.getByRole("dialog", { name: "Edit task" });
    const titleInput = within(dialog).getByDisplayValue("Original title");
    await user.clear(titleInput);
    await user.type(titleInput, "Updated title");
    await user.click(within(dialog).getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(tasksApi.updateTask).toHaveBeenCalledWith("task-1", {
        title: "Updated title",
        notes: "Original notes",
        due_date: "2026-07-21",
      });
      expect(onSaved).toHaveBeenCalled();
    });
  });

  it("shows backend validation errors", async () => {
    const user = userEvent.setup();
    vi.spyOn(tasksApi, "updateTask").mockRejectedValue(
      new Error("Only pending tasks can be edited"),
    );

    render(
      <TaskEditDialog
        open
        task={{
          id: "task-1",
          title: "Original title",
          notes: null,
          due_date: "2026-07-21",
        }}
        onClose={vi.fn()}
        onSaved={vi.fn()}
      />,
    );

    const dialog = screen.getByRole("dialog", { name: "Edit task" });
    await user.click(within(dialog).getByRole("button", { name: "Save changes" }));

    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "Only pending tasks can be edited",
    );
  });
});
