export type TaskStatus = "pending" | "completed" | "cancelled";

export interface Task {
  id: string;
  title: string;
  notes: string | null;
  due_date: string | null;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateBody {
  title: string;
  notes?: string | null;
  due_date?: string | null;
}

export interface TodayTaskItem {
  task_id: string;
  title: string;
  notes: string | null;
  due_date: string | null;
  is_overdue: boolean;
}

export interface TodayView {
  reference_date: string;
  tasks: TodayTaskItem[];
}

export interface WeekTaskItem {
  task_id: string;
  title: string;
  due_date: string | null;
  is_overdue: boolean;
}

export interface WeekDayGroup {
  date: string | null;
  tasks: WeekTaskItem[];
}

export interface WeekView {
  week_start: string;
  week_end: string;
  days: WeekDayGroup[];
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep default message when body is not JSON.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function listTasks(status?: TaskStatus): Promise<Task[]> {
  const url = status ? `/api/tasks?status=${status}` : "/api/tasks";
  const response = await fetch(url);
  return parseJson<Task[]>(response);
}

export async function createTask(body: TaskCreateBody): Promise<Task> {
  const response = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<Task>(response);
}

export async function completeTask(id: string): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}/complete`, { method: "POST" });
  return parseJson<Task>(response);
}

export async function cancelTask(id: string): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}/cancel`, { method: "POST" });
  return parseJson<Task>(response);
}

export async function fetchTodayView(date?: string): Promise<TodayView> {
  const url = date ? `/api/views/today?date=${date}` : "/api/views/today";
  const response = await fetch(url);
  return parseJson<TodayView>(response);
}

export async function fetchWeekView(weekStart?: string): Promise<WeekView> {
  const url = weekStart
    ? `/api/views/week?week_start=${weekStart}`
    : "/api/views/week";
  const response = await fetch(url);
  return parseJson<WeekView>(response);
}

export function formatDisplayDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
