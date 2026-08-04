import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MobileCaptureFab } from "./MobileCaptureFab";

vi.mock("../lib/viewport", () => ({
  useNarrowViewport: vi.fn(() => true),
}));

describe("MobileCaptureFab", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("opens capture modal on narrow viewports", async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    render(<MobileCaptureFab onCreated={onCreated} />);

    await user.click(screen.getByRole("button", { name: "Capture" }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
  });
});
