import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { MobileBottomNav } from "./MobileBottomNav";

describe("MobileBottomNav", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows primary links and opens the more menu", async () => {
    const user = userEvent.setup();
    render(<MobileBottomNav currentPath="/today" />);

    expect(screen.getByRole("link", { name: "Today" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Week" })).toHaveAttribute("href", "/week");

    await user.click(screen.getByRole("button", { name: "More" }));

    expect(screen.getByRole("heading", { name: "More" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Settings" })).toHaveAttribute(
      "href",
      "/settings",
    );
  });
});
