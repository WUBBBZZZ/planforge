import { useEffect, useState, type FormEvent } from "react";

import {
  addMaintenanceHistoricalCompletion,
  clearMaintenanceNextAction,
  clearMaintenanceSchedulingReminder,
  completeMaintenance,
  correctMaintenanceCompletion,
  formatAppointmentSchedule,
  formatDisplayDate,
  getMaintenance,
  linkMaintenanceAppointment,
  listAppointments,
  rescheduleMaintenanceAppointment,
  scheduleMaintenanceAppointment,
  setMaintenanceSchedulingReminder,
  type Appointment,
  type MaintenanceDetail,
  type MaintenanceItem,
} from "../lib/tasks";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Select } from "./Select";
import { Textarea } from "./Textarea";

export type MaintenanceActionMode =
  | "history"
  | "complete"
  | "add_historical"
  | "correct"
  | "schedule"
  | "link"
  | "reminder"
  | "clear";

export interface MaintenanceActionsDialogProps {
  open: boolean;
  item: MaintenanceItem | null;
  initialMode?: MaintenanceActionMode;
  onClose: () => void;
  onSaved: () => void;
}

const ACTION_OPTIONS: Array<{ value: MaintenanceActionMode; label: string }> = [
  { value: "history", label: "View history" },
  { value: "complete", label: "Mark completed" },
  { value: "add_historical", label: "Add historical completion" },
  { value: "correct", label: "Correct completion" },
  { value: "schedule", label: "Schedule next appointment" },
  { value: "link", label: "Link existing appointment" },
  { value: "reminder", label: "Set scheduling reminder" },
  { value: "clear", label: "Clear next action" },
];

function todayIsoDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function MaintenanceActionsForm({
  item,
  initialMode,
  onClose,
  onSaved,
}: {
  item: MaintenanceItem;
  initialMode: MaintenanceActionMode;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [mode, setMode] = useState<MaintenanceActionMode>(initialMode);
  const [detail, setDetail] = useState<MaintenanceDetail | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [completedOn, setCompletedOn] = useState(todayIsoDate());
  const [notes, setNotes] = useState("");
  const [voidReason, setVoidReason] = useState("");
  const [completionId, setCompletionId] = useState("");

  const [isAllDay, setIsAllDay] = useState(true);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [location, setLocation] = useState("");
  const [appointmentId, setAppointmentId] = useState("");
  const [reminderDate, setReminderDate] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getMaintenance(item.id), listAppointments({ filter: "upcoming" })])
      .then(([detailResult, appointmentList]) => {
        if (!cancelled) {
          setDetail(detailResult);
          setAppointments(
            appointmentList.filter(
              (appointment) =>
                appointment.maintenance_definition_id == null ||
                appointment.maintenance_definition_id === item.id,
            ),
          );
          const latestCompletion = (detailResult.completions ?? []).find(
            (completion) => !completion.is_voided,
          );
          if (latestCompletion) {
            setCompletionId(latestCompletion.id);
          }
          if (detailResult.linked_appointment) {
            const linked = detailResult.linked_appointment;
            setIsAllDay(linked.is_all_day);
            setStartDate(linked.start_date);
            setEndDate(linked.end_date);
            if (linked.starts_at) {
              const start = new Date(linked.starts_at);
              setStartTime(
                `${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")}`,
              );
            }
            if (linked.ends_at) {
              const end = new Date(linked.ends_at);
              setEndTime(
                `${String(end.getHours()).padStart(2, "0")}:${String(end.getMinutes()).padStart(2, "0")}`,
              );
            }
          }
          if (detailResult.scheduling_reminder_date) {
            setReminderDate(detailResult.scheduling_reminder_date);
          }
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Could not load maintenance details",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [item.id]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      switch (mode) {
        case "complete":
          await completeMaintenance(item.id, {
            completed_on: completedOn,
            notes: notes.trim() ? notes : null,
          });
          break;
        case "add_historical":
          await addMaintenanceHistoricalCompletion(item.id, {
            completed_on: completedOn,
            notes: notes.trim() ? notes : null,
          });
          break;
        case "correct":
          if (!completionId) {
            throw new Error("Select a completion to correct");
          }
          await correctMaintenanceCompletion(item.id, completionId, {
            completed_on: completedOn,
            notes: notes.trim() ? notes : null,
            void_reason: voidReason.trim() ? voidReason : null,
          });
          break;
        case "schedule":
          if (!startDate || !endDate) {
            throw new Error("Start and end dates are required");
          }
          if (!isAllDay && (!startTime || !endTime)) {
            throw new Error("Start and end times are required for timed appointments");
          }
          if (detail?.linked_appointment) {
            await rescheduleMaintenanceAppointment(item.id, {
              is_all_day: isAllDay,
              start_date: startDate,
              end_date: endDate,
              start_time: isAllDay ? null : startTime,
              end_time: isAllDay ? null : endTime,
            });
          } else {
            await scheduleMaintenanceAppointment(item.id, {
              title: item.title,
              notes: notes.trim() ? notes : null,
              location: location.trim() ? location : null,
              is_all_day: isAllDay,
              start_date: startDate,
              end_date: endDate,
              start_time: isAllDay ? null : startTime,
              end_time: isAllDay ? null : endTime,
            });
          }
          break;
        case "link":
          if (!appointmentId) {
            throw new Error("Select an appointment to link");
          }
          await linkMaintenanceAppointment(item.id, appointmentId);
          break;
        case "reminder":
          if (!reminderDate) {
            throw new Error("Reminder date is required");
          }
          await setMaintenanceSchedulingReminder(item.id, reminderDate);
          break;
        case "clear":
          if (detail?.scheduling_reminder_date) {
            await clearMaintenanceSchedulingReminder(item.id);
          }
          await clearMaintenanceNextAction(item.id);
          break;
        default:
          onClose();
          return;
      }
      onSaved();
      onClose();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Action failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <p className="pf-muted">Loading…</p>;
  }

  const activeCompletions = (detail?.completions ?? []).filter(
    (completion) => !completion.is_voided,
  );

  return (
    <form className="pf-task-form" onSubmit={(event) => void handleSubmit(event)}>
      <FormField label="Action">
        <Select
          value={mode}
          onChange={(event) => setMode(event.target.value as MaintenanceActionMode)}
          options={ACTION_OPTIONS}
        />
      </FormField>

      {mode === "history" ? (
        <div className="pf-maintenance-history-detail">
          {(detail?.completions ?? []).length ? (
            <ul>
              {(detail?.completions ?? []).map((completion) => (
                <li key={completion.id}>
                  {formatDisplayDate(completion.completed_on)}
                  {completion.is_voided ? " (voided)" : ""}
                  {completion.notes ? ` — ${completion.notes}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="pf-muted">No completion history yet.</p>
          )}
          {detail?.linked_appointment ? (
            <p>
              Linked appointment: {formatAppointmentSchedule(detail.linked_appointment)}
            </p>
          ) : null}
          {detail?.scheduling_reminder_date ? (
            <p>
              Scheduling reminder: {formatDisplayDate(detail.scheduling_reminder_date)}
            </p>
          ) : null}
        </div>
      ) : null}

      {mode === "complete" || mode === "add_historical" || mode === "correct" ? (
        <>
          {mode === "correct" ? (
            <FormField label="Completion to correct">
              <Select
                value={completionId}
                onChange={(event) => setCompletionId(event.target.value)}
                options={activeCompletions.map((completion) => ({
                  value: completion.id,
                  label: formatDisplayDate(completion.completed_on),
                }))}
              />
            </FormField>
          ) : null}
          <FormField label="Completed on">
            <Input
              type="date"
              value={completedOn}
              onChange={(event) => setCompletedOn(event.target.value)}
              required
            />
          </FormField>
          <FormField label="Notes">
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={2}
            />
          </FormField>
          {mode === "correct" ? (
            <FormField label="Correction reason">
              <Input
                value={voidReason}
                onChange={(event) => setVoidReason(event.target.value)}
              />
            </FormField>
          ) : null}
        </>
      ) : null}

      {mode === "schedule" ? (
        <>
          <FormField label="All day">
            <label>
              <input
                type="checkbox"
                checked={isAllDay}
                onChange={(event) => setIsAllDay(event.target.checked)}
              />{" "}
              All day
            </label>
          </FormField>
          <FormField label="Start date">
            <Input
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              required
            />
          </FormField>
          <FormField label="End date">
            <Input
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              required
            />
          </FormField>
          {!isAllDay ? (
            <>
              <FormField label="Start time">
                <Input
                  type="time"
                  value={startTime}
                  onChange={(event) => setStartTime(event.target.value)}
                  required
                />
              </FormField>
              <FormField label="End time">
                <Input
                  type="time"
                  value={endTime}
                  onChange={(event) => setEndTime(event.target.value)}
                  required
                />
              </FormField>
            </>
          ) : null}
          <FormField label="Location">
            <Input
              value={location}
              onChange={(event) => setLocation(event.target.value)}
            />
          </FormField>
          <FormField label="Notes">
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={2}
            />
          </FormField>
        </>
      ) : null}

      {mode === "link" ? (
        <FormField label="Appointment">
          <Select
            value={appointmentId}
            onChange={(event) => setAppointmentId(event.target.value)}
            options={appointments.map((appointment) => ({
              value: appointment.id,
              label: `${appointment.title} · ${formatAppointmentSchedule(appointment)}`,
            }))}
          />
        </FormField>
      ) : null}

      {mode === "reminder" ? (
        <FormField label="Remind me on">
          <Input
            type="date"
            value={reminderDate}
            onChange={(event) => setReminderDate(event.target.value)}
            required
          />
        </FormField>
      ) : null}

      {mode === "clear" ? (
        <p className="pf-muted">
          Clears any linked appointment reminder state and returns this maintenance item
          to no next date.
        </p>
      ) : null}

      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="pf-dialog__actions">
        <Button type="button" variant="ghost" onClick={onClose}>
          {mode === "history" ? "Close" : "Cancel"}
        </Button>
        {mode !== "history" ? (
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Apply"}
          </Button>
        ) : null}
      </div>
    </form>
  );
}

export function MaintenanceActionsDialog({
  open,
  item,
  initialMode = "history",
  onClose,
  onSaved,
}: MaintenanceActionsDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={item ? item.title : "Maintenance"}>
      {open && item ? (
        <MaintenanceActionsForm
          key={`${item.id}-${initialMode}`}
          item={item}
          initialMode={initialMode}
          onClose={onClose}
          onSaved={onSaved}
        />
      ) : null}
    </Dialog>
  );
}
