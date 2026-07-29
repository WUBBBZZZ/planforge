import { useState, type FormEvent } from "react";

import {
  createAppointment,
  rescheduleAppointment,
  updateAppointment,
  type Appointment,
  type AppointmentCreateBody,
} from "../lib/tasks";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Textarea } from "./Textarea";

export interface AppointmentEditDialogProps {
  open: boolean;
  appointment: Appointment | null;
  onClose: () => void;
  onSaved: () => void;
}

interface AppointmentFormProps {
  appointment?: Appointment | null;
  onClose: () => void;
  onSaved: () => void;
}

function toTimeInput(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function AppointmentForm({ appointment, onClose, onSaved }: AppointmentFormProps) {
  const isEdit = appointment != null;
  const [title, setTitle] = useState(appointment?.title ?? "");
  const [notes, setNotes] = useState(appointment?.notes ?? "");
  const [location, setLocation] = useState(appointment?.location ?? "");
  const [category, setCategory] = useState(appointment?.category ?? "");
  const [reminderMinutes, setReminderMinutes] = useState(
    appointment?.reminder_minutes?.toString() ?? "",
  );
  const [isAllDay, setIsAllDay] = useState(appointment?.is_all_day ?? false);
  const [startDate, setStartDate] = useState(appointment?.start_date ?? "");
  const [endDate, setEndDate] = useState(appointment?.end_date ?? "");
  const [startTime, setStartTime] = useState(
    toTimeInput(appointment?.starts_at ?? null),
  );
  const [endTime, setEndTime] = useState(toTimeInput(appointment?.ends_at ?? null));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      if (!startDate || !endDate) {
        throw new Error("Start and end dates are required");
      }
      if (!isAllDay && (!startTime || !endTime)) {
        throw new Error("Start and end times are required for timed appointments");
      }

      if (isEdit && appointment) {
        await updateAppointment(appointment.id, {
          title,
          notes: notes.trim() ? notes : null,
          location: location.trim() ? location : null,
          category: category.trim() ? category : null,
          reminder_minutes: reminderMinutes ? Number(reminderMinutes) : null,
        });
        await rescheduleAppointment(appointment.id, {
          is_all_day: isAllDay,
          start_date: startDate,
          end_date: endDate,
          start_time: isAllDay ? null : `${startTime}:00`,
          end_time: isAllDay ? null : `${endTime}:00`,
        });
      } else {
        const body: AppointmentCreateBody = {
          title,
          notes: notes.trim() ? notes : null,
          location: location.trim() ? location : null,
          category: category.trim() ? category : null,
          reminder_minutes: reminderMinutes ? Number(reminderMinutes) : null,
          is_all_day: isAllDay,
          start_date: startDate,
          end_date: endDate,
          start_time: isAllDay ? null : `${startTime}:00`,
          end_time: isAllDay ? null : `${endTime}:00`,
        };
        await createAppointment(body);
      }
      onSaved();
      onClose();
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Could not save appointment";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="pf-task-form" onSubmit={(event) => void handleSubmit(event)}>
      <FormField label="Title">
        <Input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
          autoFocus
        />
      </FormField>

      <FormField label="Notes">
        <Textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={3}
        />
      </FormField>

      <FormField label="Location">
        <Input value={location} onChange={(event) => setLocation(event.target.value)} />
      </FormField>

      <FormField label="Category" hint="Free-text until categories ship">
        <Input value={category} onChange={(event) => setCategory(event.target.value)} />
      </FormField>

      <FormField label="Reminder (minutes before)">
        <Input
          type="number"
          min={0}
          value={reminderMinutes}
          onChange={(event) => setReminderMinutes(event.target.value)}
        />
      </FormField>

      <div className="pf-form-field">
        <span className="pf-form-field__label">All day</span>
        <label className="pf-checkbox-row">
          <input
            type="checkbox"
            checked={isAllDay}
            onChange={(event) => setIsAllDay(event.target.checked)}
          />
          <span>All-day or multi-day event</span>
        </label>
      </div>

      <FormField label="Start date">
        <Input
          type="date"
          value={startDate}
          onChange={(event) => {
            setStartDate(event.target.value);
            if (!endDate || endDate < event.target.value) {
              setEndDate(event.target.value);
            }
          }}
          required
        />
      </FormField>

      <FormField label="End date" hint="Inclusive for all-day events">
        <Input
          type="date"
          value={endDate}
          min={startDate}
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

      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="pf-dialog__actions">
        <Button type="button" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : isEdit ? "Save changes" : "Create appointment"}
        </Button>
      </div>
    </form>
  );
}

export function AppointmentEditDialog({
  open,
  appointment,
  onClose,
  onSaved,
}: AppointmentEditDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={appointment ? "Edit appointment" : "Create appointment"}
    >
      {open ? (
        <AppointmentForm
          key={appointment?.id ?? "new"}
          appointment={appointment}
          onClose={onClose}
          onSaved={onSaved}
        />
      ) : null}
    </Dialog>
  );
}
