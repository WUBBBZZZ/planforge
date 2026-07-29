import { useState, type FormEvent } from "react";

import { createAppointment, createBacklogItem, createTask } from "../lib/tasks";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Select } from "./Select";
import { Textarea } from "./Textarea";

export type CaptureDestination = "task" | "backlog" | "appointment";

export interface CaptureModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  defaultDueDate?: string;
}

interface CaptureFormProps {
  defaultDueDate?: string;
  onClose: () => void;
  onCreated: () => void;
}

function CaptureForm({ defaultDueDate, onClose, onCreated }: CaptureFormProps) {
  const [destination, setDestination] = useState<CaptureDestination>("task");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [dueDate, setDueDate] = useState(defaultDueDate ?? "");
  const [isAllDay, setIsAllDay] = useState(false);
  const [startDate, setStartDate] = useState(defaultDueDate ?? "");
  const [endDate, setEndDate] = useState(defaultDueDate ?? "");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      if (destination === "task") {
        await createTask({
          title,
          notes: notes.trim() ? notes : null,
          due_date: dueDate || defaultDueDate || null,
        });
      } else if (destination === "backlog") {
        await createBacklogItem({
          title,
          notes: notes.trim() ? notes : null,
        });
      } else {
        if (!startDate || !endDate) {
          throw new Error("Start and end dates are required for appointments");
        }
        if (!isAllDay && (!startTime || !endTime)) {
          throw new Error("Start and end times are required for timed appointments");
        }
        await createAppointment({
          title,
          notes: notes.trim() ? notes : null,
          is_all_day: isAllDay,
          start_date: startDate,
          end_date: endDate,
          start_time: isAllDay ? null : `${startTime}:00`,
          end_time: isAllDay ? null : `${endTime}:00`,
        });
      }
      onCreated();
      onClose();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Could not save item";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="pf-task-form" onSubmit={(event) => void handleSubmit(event)}>
      <FormField label="Destination">
        <Select
          value={destination}
          onChange={(event) => setDestination(event.target.value as CaptureDestination)}
          options={[
            { value: "task", label: "Task" },
            { value: "backlog", label: "Backlog" },
            { value: "appointment", label: "Appointment" },
          ]}
        />
      </FormField>

      <FormField label="Title" hint="Fabricated example only">
        <Input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Water the plants"
          required
          autoFocus
        />
      </FormField>

      <FormField label="Notes">
        <Textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Optional demo notes"
          rows={3}
        />
      </FormField>

      {destination === "task" ? (
        <FormField label="Due date">
          <Input
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
        </FormField>
      ) : null}

      {destination === "appointment" ? (
        <>
          <FormField label="All day">
            <label className="pf-checkbox-row">
              <input
                type="checkbox"
                checked={isAllDay}
                onChange={(event) => setIsAllDay(event.target.checked)}
              />
              <span>All-day or multi-day event</span>
            </label>
          </FormField>
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
          <FormField label="End date">
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
        </>
      ) : null}

      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="pf-task-form__actions">
        <Button type="button" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}

export function CaptureModal({
  open,
  onClose,
  onCreated,
  defaultDueDate,
}: CaptureModalProps) {
  const formKey = `${defaultDueDate ?? "none"}`;

  return (
    <Dialog open={open} title="Capture" onClose={onClose}>
      {open ? (
        <CaptureForm
          key={formKey}
          defaultDueDate={defaultDueDate}
          onClose={onClose}
          onCreated={onCreated}
        />
      ) : null}
    </Dialog>
  );
}
