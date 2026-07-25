import { useState, type FormEvent } from "react";

import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Textarea } from "./Textarea";
import { createTask, type TaskCreateBody } from "../lib/tasks";

export interface TaskModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  defaultDueDate?: string;
}

export function TaskModal({
  open,
  onClose,
  onCreated,
  defaultDueDate,
}: TaskModalProps) {
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [dueDate, setDueDate] = useState(defaultDueDate ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const resetForm = () => {
    setTitle("");
    setNotes("");
    setDueDate(defaultDueDate ?? "");
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const body: TaskCreateBody = {
      title,
      notes: notes.trim() ? notes : null,
      due_date: dueDate || null,
    };

    try {
      await createTask(body);
      resetForm();
      onCreated();
      onClose();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Could not create task";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} title="Add task" onClose={handleClose}>
      <form className="pf-task-form" onSubmit={handleSubmit}>
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

        <FormField label="Due date">
          <Input
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
        </FormField>

        {error ? (
          <p className="pf-form-field__error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="pf-task-form__actions">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Create task"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
