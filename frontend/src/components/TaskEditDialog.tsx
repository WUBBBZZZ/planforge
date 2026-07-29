import { useState, type FormEvent } from "react";

import { updateTask, type Task } from "../lib/tasks";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Textarea } from "./Textarea";

export interface TaskEditDialogProps {
  open: boolean;
  task: Pick<Task, "id" | "title" | "notes" | "due_date"> | null;
  onClose: () => void;
  onSaved: () => void;
  onMoveToBacklog?: () => void;
}

interface TaskEditFormProps {
  task: Pick<Task, "id" | "title" | "notes" | "due_date">;
  onClose: () => void;
  onSaved: () => void;
  onMoveToBacklog?: () => void;
}

function TaskEditForm({ task, onClose, onSaved, onMoveToBacklog }: TaskEditFormProps) {
  const [title, setTitle] = useState(task.title);
  const [notes, setNotes] = useState(task.notes ?? "");
  const [dueDate, setDueDate] = useState(task.due_date ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await updateTask(task.id, {
        title,
        notes: notes.trim() ? notes : null,
        due_date: dueDate || null,
      });
      onSaved();
      onClose();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Could not update task";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="pf-task-form" onSubmit={handleSubmit}>
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

      <FormField
        label="Due date"
        hint={
          !dueDate && onMoveToBacklog
            ? "Clear the due date to unschedule, or move this task to the backlog."
            : undefined
        }
      >
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
        {onMoveToBacklog ? (
          <Button
            type="button"
            variant="ghost"
            disabled={submitting}
            onClick={() => onMoveToBacklog()}
          >
            Move to backlog
          </Button>
        ) : null}
        <Button type="button" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}

export function TaskEditDialog({
  open,
  task,
  onClose,
  onSaved,
  onMoveToBacklog,
}: TaskEditDialogProps) {
  return (
    <Dialog open={open} title="Edit task" onClose={onClose}>
      {task ? (
        <TaskEditForm
          key={task.id}
          task={task}
          onClose={onClose}
          onSaved={onSaved}
          onMoveToBacklog={onMoveToBacklog}
        />
      ) : null}
    </Dialog>
  );
}
