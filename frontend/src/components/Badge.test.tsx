import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders label text", () => {
    render(<Badge tone="success">Completed</Badge>);
    expect(screen.getByText("Completed")).toBeVisible();
  });
});
