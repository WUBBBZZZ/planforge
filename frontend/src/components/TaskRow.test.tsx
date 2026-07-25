import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TaskRow } from "./TaskRow";

describe("TaskRow", () => {
  it("renders and fires complete callback", async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn().mockResolvedValue(undefined);

    render(
      <TaskRow
        taskId="task-1"
        title="Water the plants"
        dueDate="2026-07-21"
        onComplete={onComplete}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText("Water the plants")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Complete" }));
    expect(onComplete).toHaveBeenCalledWith("task-1");
  });
});
