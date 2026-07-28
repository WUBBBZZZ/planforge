import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormField } from "./FormField";
import { Input } from "./Input";

describe("FormField", () => {
  it("associates the label with a child control", () => {
    render(
      <FormField label="Title">
        <Input data-testid="title-input" />
      </FormField>,
    );

    const input = screen.getByTestId("title-input");
    const label = screen.getByText("Title");
    expect(label).toHaveAttribute("for", input.id);
    expect(input.id).toBeTruthy();
  });
});
