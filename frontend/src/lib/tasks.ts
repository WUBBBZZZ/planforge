import {
  parseApiJson,
  type AppointmentResponse,
  type BacklogItemResponse,
  type MaintenanceCompletionResponse,
  type MaintenanceDetailResponse,
  type MaintenanceResponse,
  type MonthViewResponse,
  type RoutineResponse,
  type TaskResponse,
  type TodayViewResponse,
  type WeekViewResponse,
  type WeeklyTargetResponse,
} from "../api/client";

export { ApiError } from "../api/client";

export type ViewItemKind = "task" | "occurrence" | "appointment" | "maintenance";

export type TaskStatus = TaskResponse["status"];

export type Task = TaskResponse;

export interface TaskCreateBody {
  title: string;
  notes?: string | null;
  due_date?: string | null;
}

export interface TaskUpdateBody {
  title?: string;
  notes?: string | null;
  due_date?: string | null;
}

export interface MoveTaskToBacklogResult {
  task: Task;
  backlog_item: BacklogItem;
}

export type PlannerItem = {
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
  occurrence_role?: string | null;
  is_all_day?: boolean;
  span_start_date?: string | null;
  span_end_date?: string | null;
  span_segment?: string | null;
  location?: string | null;
  status?: string | null;
};

export type TodayView = TodayViewResponse;
export type WeekView = WeekViewResponse;
export type MonthView = MonthViewResponse;

export type BacklogItem = BacklogItemResponse;
export type Routine = RoutineResponse;
export type Appointment = AppointmentResponse;

export type AppointmentListFilter =
  "upcoming" | "today" | "past" | "cancelled" | "archived" | "scheduled" | "completed";

export interface AppointmentCreateBody {
  title: string;
  notes?: string | null;
  location?: string | null;
  category?: string | null;
  reminder_minutes?: number | null;
  maintenance_definition_id?: string | null;
  is_all_day: boolean;
  start_date: string;
  end_date: string;
  start_time?: string | null;
  end_time?: string | null;
}

export interface AppointmentUpdateBody {
  title?: string;
  notes?: string | null;
  location?: string | null;
  category?: string | null;
  reminder_minutes?: number | null;
  maintenance_definition_id?: string | null;
}

export interface AppointmentRescheduleBody {
  is_all_day: boolean;
  start_date: string;
  end_date: string;
  start_time?: string | null;
  end_time?: string | null;
}

export type MaintenanceItem = MaintenanceResponse;
export type MaintenanceCompletion = MaintenanceCompletionResponse;
export type MaintenanceDetail = MaintenanceDetailResponse;

export type MaintenanceListFilter =
  | "overdue"
  | "due_soon"
  | "needs_scheduling"
  | "scheduled_upcoming"
  | "active"
  | "archived";

export interface MaintenanceHistoryRow {
  maintenance: MaintenanceItem;
  current_next_label: string;
  completions: MaintenanceCompletion[];
  linked_appointment: Appointment | null;
}

export interface MaintenanceHistoryBoardData {
  rows: MaintenanceHistoryRow[];
  history_limit: number;
}

export type WeeklyTarget = WeeklyTargetResponse;

export async function syncRoutineOccurrences(): Promise<void> {
  const response = await fetch("/api/routines/sync-occurrences", { method: "POST" });
  if (!response.ok) {
    await parseApiJson(response);
  }
}

export async function listTasks(status?: TaskStatus): Promise<Task[]> {
  const url = status ? `/api/tasks?status=${status}` : "/api/tasks";
  const response = await fetch(url);
  return parseApiJson<Task[]>(response);
}

export async function createTask(body: TaskCreateBody): Promise<Task> {
  const response = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Task>(response);
}

export async function completeTask(id: string): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}/complete`, { method: "POST" });
  return parseApiJson<Task>(response);
}

export async function cancelTask(id: string): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}/cancel`, { method: "POST" });
  return parseApiJson<Task>(response);
}

export async function updateTask(id: string, body: TaskUpdateBody): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Task>(response);
}

export async function reopenTask(id: string): Promise<Task> {
  const response = await fetch(`/api/tasks/${id}/reopen`, { method: "POST" });
  return parseApiJson<Task>(response);
}

export async function moveTaskToBacklog(id: string): Promise<MoveTaskToBacklogResult> {
  const response = await fetch(`/api/tasks/${id}/move-to-backlog`, { method: "POST" });
  return parseApiJson<MoveTaskToBacklogResult>(response);
}

export async function fetchTodayView(date?: string): Promise<TodayView> {
  const url = date ? `/api/views/today?date=${date}` : "/api/views/today";
  const response = await fetch(url);
  return parseApiJson<TodayView>(response);
}

export async function fetchWeekView(weekStart?: string): Promise<WeekView> {
  const url = weekStart ? `/api/views/week?week_start=${weekStart}` : "/api/views/week";
  const response = await fetch(url);
  return parseApiJson<WeekView>(response);
}

export async function fetchMonthView(month?: string): Promise<MonthView> {
  const url = month ? `/api/views/month?month=${month}` : "/api/views/month";
  const response = await fetch(url);
  return parseApiJson<MonthView>(response);
}

export async function listBacklog(): Promise<BacklogItem[]> {
  const response = await fetch("/api/backlog");
  return parseApiJson<BacklogItem[]>(response);
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
  return parseApiJson<BacklogItem>(response);
}

export async function archiveBacklogItem(id: string): Promise<BacklogItem> {
  const response = await fetch(`/api/backlog/${id}/archive`, { method: "POST" });
  return parseApiJson<BacklogItem>(response);
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
  return parseApiJson<{ backlog: BacklogItem; task: Task }>(response);
}

export async function listRoutines(): Promise<Routine[]> {
  const response = await fetch("/api/routines");
  return parseApiJson<Routine[]>(response);
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
  return parseApiJson<Routine>(response);
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
  return parseApiJson<Routine>(response);
}

export async function pauseRoutine(id: string): Promise<Routine> {
  const response = await fetch(`/api/routines/${id}/pause`, { method: "POST" });
  return parseApiJson<Routine>(response);
}

export async function resumeRoutine(id: string): Promise<Routine> {
  const response = await fetch(`/api/routines/${id}/resume`, { method: "POST" });
  return parseApiJson<Routine>(response);
}

export async function completeOccurrence(id: string): Promise<void> {
  const response = await fetch(`/api/routines/occurrences/${id}/complete`, {
    method: "POST",
  });
  await parseApiJson(response);
}

export async function skipOccurrence(id: string): Promise<void> {
  const response = await fetch(`/api/routines/occurrences/${id}/skip`, {
    method: "POST",
  });
  await parseApiJson(response);
}

export type RoutineGroup = {
  id: string;
  name: string;
  sort_order: number;
  week_visible: boolean;
  is_system: boolean;
};

export type RoutineGroupBoard = RoutineGroup & {
  routines: Routine[];
};

export async function fetchRoutineGroupBoard(): Promise<RoutineGroupBoard[]> {
  const response = await fetch("/api/routine-groups/board");
  return parseApiJson<RoutineGroupBoard[]>(response);
}

export async function listRoutineGroups(): Promise<RoutineGroup[]> {
  const response = await fetch("/api/routine-groups");
  return parseApiJson<RoutineGroup[]>(response);
}

export async function createRoutineGroup(name: string): Promise<RoutineGroup> {
  const response = await fetch("/api/routine-groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return parseApiJson<RoutineGroup>(response);
}

export async function updateRoutineGroup(
  id: string,
  body: { name?: string; week_visible?: boolean },
): Promise<RoutineGroup> {
  const response = await fetch(`/api/routine-groups/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<RoutineGroup>(response);
}

export async function deleteRoutineGroup(id: string): Promise<void> {
  const response = await fetch(`/api/routine-groups/${id}`, { method: "DELETE" });
  await parseApiJson(response);
}

export async function reorderRoutineGroups(groupIds: string[]): Promise<RoutineGroup[]> {
  const response = await fetch("/api/routine-groups/reorder", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_ids: groupIds }),
  });
  return parseApiJson<RoutineGroup[]>(response);
}

export async function reorderRoutinesInGroup(
  groupId: string,
  routineIds: string[],
): Promise<Routine[]> {
  const response = await fetch(`/api/routine-groups/${groupId}/routines/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ routine_ids: routineIds }),
  });
  return parseApiJson<Routine[]>(response);
}

export async function moveRoutineToGroup(
  routineId: string,
  body: { group_id: string; sort_order: number },
): Promise<Routine> {
  const response = await fetch(`/api/routine-groups/routines/${routineId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Routine>(response);
}

export async function listAppointments(options?: {
  filter?: AppointmentListFilter;
  status?: Appointment["status"];
  search?: string;
}): Promise<Appointment[]> {
  const params = new URLSearchParams();
  if (options?.filter) {
    params.set("filter", options.filter);
  }
  if (options?.status) {
    params.set("status", options.status);
  }
  if (options?.search) {
    params.set("search", options.search);
  }
  const query = params.toString();
  const url = query ? `/api/appointments?${query}` : "/api/appointments";
  const response = await fetch(url);
  return parseApiJson<Appointment[]>(response);
}

export async function getAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}`);
  return parseApiJson<Appointment>(response);
}

export async function createAppointment(
  body: AppointmentCreateBody,
): Promise<Appointment> {
  const response = await fetch("/api/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Appointment>(response);
}

export async function updateAppointment(
  id: string,
  body: AppointmentUpdateBody,
): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Appointment>(response);
}

export async function rescheduleAppointment(
  id: string,
  body: AppointmentRescheduleBody,
): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/reschedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<Appointment>(response);
}

export async function completeAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/complete`, {
    method: "POST",
  });
  return parseApiJson<Appointment>(response);
}

export async function cancelAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/cancel`, { method: "POST" });
  return parseApiJson<Appointment>(response);
}

export async function reopenAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/reopen`, { method: "POST" });
  return parseApiJson<Appointment>(response);
}

export async function archiveAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/archive`, { method: "POST" });
  return parseApiJson<Appointment>(response);
}

export async function restoreAppointment(id: string): Promise<Appointment> {
  const response = await fetch(`/api/appointments/${id}/restore`, { method: "POST" });
  return parseApiJson<Appointment>(response);
}

export async function deleteAppointment(id: string): Promise<void> {
  const response = await fetch(`/api/appointments/${id}`, { method: "DELETE" });
  if (!response.ok) {
    await parseApiJson(response);
  }
}

export async function listMaintenance(options?: {
  filter?: MaintenanceListFilter;
  status?: MaintenanceItem["status"];
}): Promise<MaintenanceItem[]> {
  const params = new URLSearchParams();
  if (options?.filter) {
    params.set("filter", options.filter);
  }
  if (options?.status) {
    params.set("status", options.status);
  }
  const query = params.toString();
  const url = query ? `/api/maintenance?${query}` : "/api/maintenance";
  const response = await fetch(url);
  return parseApiJson<MaintenanceItem[]>(response);
}

export async function fetchMaintenanceHistoryBoard(
  historyLimit = 10,
): Promise<MaintenanceHistoryBoardData> {
  const response = await fetch(
    `/api/maintenance/history-board?history_limit=${historyLimit}`,
  );
  return parseApiJson<MaintenanceHistoryBoardData>(response);
}

export async function getMaintenance(
  id: string,
  historyLimit = 25,
): Promise<MaintenanceDetail> {
  const response = await fetch(`/api/maintenance/${id}?history_limit=${historyLimit}`);
  return parseApiJson<MaintenanceDetail>(response);
}

export async function createMaintenance(body: {
  title: string;
  category?: string | null;
  notes?: string | null;
  interval_unit?: MaintenanceItem["interval_unit"];
  interval_value?: number | null;
  lead_time_days?: number;
  reminder_offset_days?: number | null;
}): Promise<MaintenanceItem> {
  const response = await fetch("/api/maintenance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function updateMaintenance(
  id: string,
  body: Partial<{
    title: string;
    category: string | null;
    notes: string | null;
    interval_unit: MaintenanceItem["interval_unit"];
    interval_value: number | null;
    lead_time_days: number;
    reminder_offset_days: number | null;
  }>,
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function completeMaintenance(
  id: string,
  body?: { completed_on?: string; notes?: string | null },
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function archiveMaintenance(id: string): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/archive`, { method: "POST" });
  return parseApiJson<MaintenanceItem>(response);
}

export async function restoreMaintenance(id: string): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/restore`, { method: "POST" });
  return parseApiJson<MaintenanceItem>(response);
}

export async function addMaintenanceHistoricalCompletion(
  id: string,
  body: { completed_on: string; notes?: string | null },
): Promise<MaintenanceCompletion> {
  const response = await fetch(`/api/maintenance/${id}/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<MaintenanceCompletion>(response);
}

export async function scheduleMaintenanceAppointment(
  id: string,
  body: {
    title?: string | null;
    notes?: string | null;
    location?: string | null;
    is_all_day: boolean;
    start_date: string;
    end_date: string;
    start_time?: string | null;
    end_time?: string | null;
  },
): Promise<MaintenanceDetail> {
  const response = await fetch(`/api/maintenance/${id}/schedule-appointment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<MaintenanceDetail>(response);
}

export async function setMaintenanceSchedulingReminder(
  id: string,
  reminderDate: string,
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/scheduling-reminder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reminder_date: reminderDate }),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function clearMaintenanceSchedulingReminder(
  id: string,
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/scheduling-reminder`, {
    method: "DELETE",
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function linkMaintenanceAppointment(
  id: string,
  appointmentId: string,
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/link-appointment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appointment_id: appointmentId }),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function rescheduleMaintenanceAppointment(
  id: string,
  body: {
    is_all_day: boolean;
    start_date: string;
    end_date: string;
    start_time?: string | null;
    end_time?: string | null;
  },
): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/reschedule-appointment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseApiJson<MaintenanceItem>(response);
}

export async function correctMaintenanceCompletion(
  maintenanceId: string,
  completionId: string,
  body: { completed_on: string; notes?: string | null; void_reason?: string | null },
): Promise<MaintenanceCompletion> {
  const response = await fetch(
    `/api/maintenance/${maintenanceId}/completions/${completionId}/correct`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  return parseApiJson<MaintenanceCompletion>(response);
}

export async function clearMaintenanceNextAction(id: string): Promise<MaintenanceItem> {
  const response = await fetch(`/api/maintenance/${id}/clear-next-action`, {
    method: "POST",
  });
  return parseApiJson<MaintenanceItem>(response);
}

export function maintenanceNextActionLabel(item: MaintenanceItem): string {
  switch (item.next_action_status) {
    case "scheduled":
      return "Scheduled";
    case "needs_scheduling":
      return item.next_due_date
        ? `Due ${formatDisplayDate(item.next_due_date)}`
        : "Needs scheduling";
    case "reminder_set":
      return item.scheduling_reminder_date
        ? `Remind ${formatDisplayDate(item.scheduling_reminder_date)}`
        : "Reminder set";
    case "not_applicable":
      return "Archived";
    default:
      return "No next date";
  }
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
  return parseApiJson<WeeklyTarget>(response);
}

export async function logWeeklyTargetProgress(id: string): Promise<WeeklyTarget> {
  const response = await fetch(`/api/weekly-targets/${id}/progress`, {
    method: "POST",
  });
  return parseApiJson<WeeklyTarget>(response);
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
  return parseApiJson<WeeklyTarget>(response);
}

export async function deleteWeeklyTarget(id: string): Promise<void> {
  const response = await fetch(`/api/weekly-targets/${id}`, { method: "DELETE" });
  if (!response.ok) {
    await parseApiJson(response);
  }
}

export async function fetchSettings(): Promise<Record<string, string>> {
  const response = await fetch("/api/settings");
  const payload = await parseApiJson<{ settings: Record<string, string> }>(response);
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
  const payload = await parseApiJson<{ settings: Record<string, string> }>(response);
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

export function formatAppointmentSchedule(appointment: Appointment): string {
  if (appointment.is_all_day) {
    if (appointment.start_date === appointment.end_date) {
      return `All day · ${formatDisplayDate(appointment.start_date)}`;
    }
    return `All day · ${formatDisplayDate(appointment.start_date)} – ${formatDisplayDate(appointment.end_date)}`;
  }
  if (appointment.starts_at && appointment.ends_at) {
    return `${formatDisplayDate(appointment.start_date)} · ${formatTimeRange(appointment.starts_at, appointment.ends_at)}`;
  }
  return formatDisplayDate(appointment.start_date);
}

export function appointmentStatusLabel(status: Appointment["status"]): string {
  switch (status) {
    case "scheduled":
      return "Scheduled";
    case "completed":
      return "Completed";
    case "cancelled":
      return "Cancelled";
    case "archived":
      return "Archived";
  }
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
