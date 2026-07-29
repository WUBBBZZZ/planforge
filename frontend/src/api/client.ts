import type { components } from "./schema";

export type ApiComponents = components;

export type TaskResponse = components["schemas"]["TaskResponse"];
export type AppointmentResponse = components["schemas"]["AppointmentResponse"];
export type MaintenanceResponse = components["schemas"]["MaintenanceResponse"];
export type MaintenanceDetailResponse =
  components["schemas"]["MaintenanceDetailResponse"];
export type MaintenanceCompletionResponse =
  components["schemas"]["MaintenanceCompletionResponse"];
export type BacklogItemResponse = components["schemas"]["BacklogItemResponse"];
export type RoutineResponse = components["schemas"]["RoutineResponse"];
export type WeeklyTargetResponse = components["schemas"]["WeeklyTargetResponse"];
export type TodayViewResponse = components["schemas"]["TodayViewResponse"];
export type WeekViewResponse = components["schemas"]["WeekViewResponse"];
export type MonthViewResponse = components["schemas"]["MonthViewResponse"];
export type SettingsResponse = components["schemas"]["SettingsResponse"];

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function formatDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => {
        if (typeof entry === "object" && entry != null && "msg" in entry) {
          return String((entry as { msg: unknown }).msg);
        }
        return null;
      })
      .filter((value): value is string => value != null);
    return messages.length > 0 ? messages.join(", ") : null;
  }
  return null;
}

export async function parseApiJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      const formatted = formatDetail(payload.detail);
      if (formatted) {
        message = formatted;
      }
    } catch {
      // Keep default message when body is not JSON.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}
