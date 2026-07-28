export type ViewItemKind = "task" | "occurrence" | "appointment" | "maintenance";

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

export interface PlannerItem {
  kind: ViewItemKind;
  item_id: string;
  title: string;
  notes?: string | null;
  due_date: string | null;
  starts_at: string | null;
  ends_at: string | null;
  is_overdue: boolean;
  is_completed?: boolean;
  routine_title?: string | null;
}

export interface TodayView {
  reference_date: string;
  items: PlannerItem[];
}

export interface WeekDayGroup {
  date: string | null;
  items: PlannerItem[];
  label?: string | null;
}

export interface WeekTargetSummary {
  target_id: string;
  title: string;
  completed_count: number;
  target_count: number;
}

export interface WeekView {
  week_start: string;
  week_end: string;
  days: WeekDayGroup[];
  targets: WeekTargetSummary[];
}

export interface MonthView {
  month: string;
  month_start: string;
  month_end: string;
  week_start_day: string;
  days: WeekDayGroup[];
}

export interface BacklogItem {
  id: string;
  title: string;
  notes: string | null;
  status: "active" | "promoted" | "archived";
  promoted_entity_type: string | null;
  promoted_entity_id: string | null;
}

export interface Routine {
  id: string;
  title: string;
  notes: string | null;
  schedule_type: "weekly" | "monthly";
  days_of_week: number[];
  day_of_month: number | null;
  interval_weeks: number;
  starts_on: string | null;
  status: "active" | "paused" | "archived";
}

export interface Appointment {
  id: string;
  title: string;
  notes: string | null;
  starts_at: string;
  ends_at: string;
  status: "scheduled" | "completed" | "cancelled";
}

export interface MaintenanceItem {
  id: string;
  title: string;
  notes: string | null;
  interval_days: number;
  next_due_date: string | null;
  status: "active" | "paused" | "archived";
}

export interface WeeklyTarget {
  id: string;
  title: string;
  target_count: number;
  status: "active" | "met" | "unmet";
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
  const url = weekStart ? `/api/views/week?week_start=${weekStart}` : "/api/views/week";
  const response = await fetch(url);
  return parseJson<WeekView>(response);
}

export async function fetchMonthView(month?: string): Promise<MonthView> {
  const url = month ? `/api/views/month?month=${month}` : "/api/views/month";
  const response = await fetch(url);
  return parseJson<MonthView>(response);
}

export async function listBacklog(): Promise<BacklogItem[]> {
  const response = await fetch("/api/backlog");
  return parseJson<BacklogItem[]>(response);
}

export async function createBacklogItem(body: {
  title: string;
  notes?: string | null;
}): Promise<BacklogItem> {
  const response = await fetch("/api/backlog", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<BacklogItem>(response);
}

export async function archiveBacklogItem(id: string): Promise<BacklogItem> {
  const response = await fetch(`/api/backlog/${id}/archive`, { method: "POST" });
  return parseJson<BacklogItem>(response);
}

export async function promoteBacklogItem(
  id: string,
  dueDate: string,
): Promise<{ backlog: BacklogItem; task: Task }> {
  const response = await fetch(`/api/backlog/${id}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ due_date: dueDate }),
  });
  return parseJson<{ backlog: BacklogItem; task: Task }>(response);
}

export async function listRoutines(): Promise<Routine[]> {
  const response = await fetch("/api/routines");
  return parseJson<Routine[]>(response);
}

export async function createRoutine(body: {
  title: string;
  notes?: string | null;
  schedule_type?: "weekly" | "monthly";
  days_of_week?: number[];
  day_of_month?: number | null;
  interval_weeks?: number;
  starts_on?: string | null;
}): Promise<Routine> {
  const response = await fetch("/api/routines", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<Routine>(response);
}

export async function updateRoutine(
  id: string,
  body: {
    title?: string;
    notes?: string | null;
    schedule_type?: "weekly" | "monthly";
    days_of_week?: number[];
    day_of_month?: number | null;
    interval_weeks?: number;
    starts_on?: string | null;
  },
): Promise<Routine> {
  const response = await fetch(`/api/routines/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<Routine>(response);
}

export async function pauseRoutine(id: string): Promise<Routine> {
  const response = await fetch(`/api/routines/${id}/pause`, { method: "POST" });
  return parseJson<Routine>(response);
}

export async function resumeRoutine(id: string): Promise<Routine> {
  const response = await fetch(`/api/routines/${id}/resume`, { method: "POST" });
  return parseJson<Routine>(response);
}

export async function completeOccurrence(id: string): Promise<void> {
  const response = await fetch(`/api/routines/occurrences/${id}/complete`, {
    method: "POST",
  });
  await parseJson(response);
}

export async function skipOccurrence(id: string): Promise<void> {
  const response = await fetch(`/api/routines/occurrences/${id}/skip`, {
    method: "POST",
  });
  await parseJson(response);
}

export async function createAppointment(body: {
  title: string;
  notes?: string | null;
  starts_at: string;
  ends_at: string;
}): Promise<Appointment> {
  const response = await fetch("/api/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<Appointment>(response);
}

export async function completeAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/complete`, {
    method: "POST",
  });
  return parseJson<Appointment>(response);
}

export async function cancelAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/cancel`, { method: "POST" });
  return parseJson<Appointment>(response);
}

export async function listMaintenance(): Promise<MaintenanceItem[]> {
  const response = await fetch("/api/maintenance");
  return parseJson<MaintenanceItem[]>(response);
}

export async function createMaintenance(body: {
  title: string;
  notes?: string | null;
  interval_days?: number;
  next_due_date?: string;
}): Promise<MaintenanceItem> {
  const response = await fetch("/api/maintenance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<MaintenanceItem>(response);
}

export async function completeMaintenance(id: string): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/complete`, { method: "POST" });
  return parseJson<MaintenanceItem>(response);
}

export async function createWeeklyTarget(body: {
  title: string;
  target_count?: number;
}): Promise<WeeklyTarget> {
  const response = await fetch("/api/weekly-targets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<WeeklyTarget>(response);
}

export async function logWeeklyTargetProgress(id: string): Promise<WeeklyTarget> {
  const response = await fetch(`/api/weekly-targets/${id}/progress`, {
    method: "POST",
  });
  return parseJson<WeeklyTarget>(response);
}

export async function updateWeeklyTarget(
  id: string,
  body: { title?: string; target_count?: number },
): Promise<WeeklyTarget> {
  const response = await fetch(`/api/weekly-targets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<WeeklyTarget>(response);
}

export async function deleteWeeklyTarget(id: string): Promise<void> {
  const response = await fetch(`/api/weekly-targets/${id}`, { method: "DELETE" });
  if (!response.ok) {
    await parseJson(response);
  }
}

export async function fetchSettings(): Promise<Record<string, string>> {
  const response = await fetch("/api/settings");
  const payload = await parseJson<{ settings: Record<string, string> }>(response);
  return payload.settings;
}

export async function updateSetting(
  key: string,
  value: string,
): Promise<Record<string, string>> {
  const response = await fetch(`/api/settings/${encodeURIComponent(key)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });
  const payload = await parseJson<{ settings: Record<string, string> }>(response);
  return payload.settings;
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

export function formatTimeRange(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  return `${start.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })} – ${end.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}`;
}

export function itemKindLabel(kind: ViewItemKind): string {
  switch (kind) {
    case "task":
      return "Task";
    case "occurrence":
      return "Routine";
    case "appointment":
      return "Appointment";
    case "maintenance":
      return "Maintenance";
  }
}
