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
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
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
        if (!startsAt || !endsAt) {
          throw new Error("Start and end times are required for appointments");
        }
        await createAppointment({
          title,
          notes: notes.trim() ? notes : null,
          starts_at: new Date(startsAt).toISOString(),
          ends_at: new Date(endsAt).toISOString(),
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
          <FormField label="Starts at">
            <Input
              type="datetime-local"
              value={startsAt}
              onChange={(event) => setStartsAt(event.target.value)}
              required
            />
          </FormField>
          <FormField label="Ends at">
            <Input
              type="datetime-local"
              value={endsAt}
              onChange={(event) => setEndsAt(event.target.value)}
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
