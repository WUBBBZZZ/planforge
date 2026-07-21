import { render } from "@testing-library/react";
import { screen } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Button } from "./Button";

describe("Button", () => {
  it("renders label and handles click", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();

    render(<Button onClick={onClick}>Save example task</Button>);

    const button = screen.getByRole("button", { name: "Save example task" });
    await user.click(button);

    expect(onClick).toHaveBeenCalledOnce();
  });
});
