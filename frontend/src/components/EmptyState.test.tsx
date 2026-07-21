import { render } from "@testing-library/react";
import { screen } from "@testing-library/dom";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        title="No example tasks"
        description="Fabricated demo data will appear here later."
      />,
    );

    expect(screen.getByRole("heading", { name: "No example tasks" })).toBeVisible();
    expect(
      screen.getByText("Fabricated demo data will appear here later."),
    ).toBeVisible();
  });
});
