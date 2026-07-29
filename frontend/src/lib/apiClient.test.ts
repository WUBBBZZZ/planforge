import { describe, expect, it } from "vitest";

import { ApiError, parseApiJson } from "../api/client";

describe("parseApiJson", () => {
  it("returns parsed JSON for successful responses", async () => {
    const response = new Response(JSON.stringify({ status: "ok" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });

    await expect(parseApiJson<{ status: string }>(response)).resolves.toEqual({
      status: "ok",
    });
  });

  it("throws ApiError with string detail", async () => {
    const response = new Response(JSON.stringify({ detail: "Task not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });

    await expect(parseApiJson(response)).rejects.toMatchObject({
      name: "ApiError",
      message: "Task not found",
      status: 404,
    });
    await expect(parseApiJson(response)).rejects.toBeInstanceOf(ApiError);
  });

  it("throws ApiError with validation detail array", async () => {
    const response = new Response(
      JSON.stringify({
        detail: [{ type: "missing", loc: ["body", "title"], msg: "Field required" }],
      }),
      { status: 422, headers: { "Content-Type": "application/json" } },
    );

    await expect(parseApiJson(response)).rejects.toMatchObject({
      status: 422,
      message: "Field required",
    });
  });

  it("uses a generic message for non-JSON error bodies", async () => {
    const response = new Response("upstream failure", { status: 500 });

    await expect(parseApiJson(response)).rejects.toMatchObject({
      status: 500,
      message: "Request failed with status 500",
    });
  });
});
