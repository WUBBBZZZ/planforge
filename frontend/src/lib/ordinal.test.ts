import { describe, expect, it } from "vitest";

import { formatDayOfMonth, ordinalSuffix } from "./ordinal";

describe("ordinal", () => {
  it.each([
    [1, "st"],
    [2, "nd"],
    [3, "rd"],
    [4, "th"],
    [11, "th"],
    [12, "th"],
    [13, "th"],
    [21, "st"],
    [22, "nd"],
    [23, "rd"],
    [31, "st"],
  ])("formats %i as %s", (day, suffix) => {
    expect(ordinalSuffix(day)).toBe(suffix);
    expect(formatDayOfMonth(day)).toBe(`${day}${suffix}`);
  });
});
