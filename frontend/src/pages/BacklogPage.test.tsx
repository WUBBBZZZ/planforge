import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { BacklogPage } from "./BacklogPage";

describe("BacklogPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("creates a backlog item from the capture form", async () => {
    const user = userEvent.setup();
    vi.spyOn(tasksApi, "listBacklog")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: "backlog-1",
          title: "Read the docs",
          notes: null,
          status: "active",
          source_entity_type: null,
          source_entity_id: null,
          promoted_entity_type: null,
          promoted_entity_id: null,
        },
      ]);
    const createBacklogItem = vi
      .spyOn(tasksApi, "createBacklogItem")
      .mockResolvedValue({
        id: "backlog-1",
        title: "Read the docs",
        notes: null,
        status: "active",
        source_entity_type: null,
        source_entity_id: null,
        promoted_entity_type: null,
        promoted_entity_id: null,
      });

    render(<BacklogPage />);

    await screen.findByText("Backlog is empty");

    await user.type(screen.getByLabelText("Title"), "Read the docs");
    await user.click(screen.getByRole("button", { name: "Add to backlog" }));

    await waitFor(() => {
      expect(createBacklogItem).toHaveBeenCalledWith({
        title: "Read the docs",
        notes: null,
      });
    });

    expect(await screen.findByText("Read the docs")).toBeInTheDocument();
  });

  it("deletes a backlog item after confirmation", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.spyOn(tasksApi, "listBacklog")
      .mockResolvedValueOnce([
        {
          id: "backlog-1",
          title: "Read the docs",
          notes: null,
          status: "active",
          source_entity_type: null,
          source_entity_id: null,
          promoted_entity_type: null,
          promoted_entity_id: null,
        },
      ])
      .mockResolvedValueOnce([]);
    const deleteBacklogItem = vi
      .spyOn(tasksApi, "deleteBacklogItem")
      .mockResolvedValue(undefined);

    render(<BacklogPage />);

    await screen.findByText("Read the docs");
    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(deleteBacklogItem).toHaveBeenCalledWith("backlog-1");
    });
  });
});
