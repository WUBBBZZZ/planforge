import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App routing", () => {
  it("shows not found for unknown routes", () => {
    window.history.pushState({}, "", "/does-not-exist");
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not found" }),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Week view" })).toHaveAttribute(
      "href",
      "/week",
    );
  });
});
