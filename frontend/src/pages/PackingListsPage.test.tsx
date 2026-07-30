import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as tasksApi from "../lib/tasks";
import { PackingListsPage } from "./PackingListsPage";

describe("PackingListsPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("creates a list and shows it as a tab", async () => {
    const user = userEvent.setup();
    vi.spyOn(tasksApi, "listPackingLists")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: "list-1",
          title: "Beach trip",
          notes: null,
          sort_order: 0,
          item_count: 0,
          question_count: 0,
        },
      ]);
    vi.spyOn(tasksApi, "createPackingList").mockResolvedValue({
      id: "list-1",
      title: "Beach trip",
      notes: null,
      sort_order: 0,
      entries: [],
    });
    vi.spyOn(tasksApi, "fetchPackingList").mockResolvedValue({
      id: "list-1",
      title: "Beach trip",
      notes: null,
      sort_order: 0,
      entries: [],
    });

    render(<PackingListsPage />);

    expect(await screen.findByText("No packing lists yet")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Trip or event name"), "Beach trip");
    await user.click(screen.getByRole("button", { name: "Create list" }));

    expect(await screen.findByRole("tab", { name: "Beach trip" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Beach trip" })).toBeInTheDocument();
  });
});
