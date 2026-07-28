import { useState, type FormEvent } from "react";

import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";

export interface WeeklyTargetDraft {
  targetId?: string;
  title: string;
  targetCount: number;
}

interface WeeklyTargetFormProps {
  draft: WeeklyTargetDraft;
  onClose: () => void;
  onSave: (draft: WeeklyTargetDraft) => Promise<void>;
}

function WeeklyTargetForm({ draft, onClose, onSave }: WeeklyTargetFormProps) {
  const [title, setTitle] = useState(draft.title);
  const [targetCount, setTargetCount] = useState(String(draft.targetCount));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const cleanedTitle = title.trim();
    const parsedCount = Number.parseInt(targetCount, 10);
    if (!cleanedTitle) {
      setError("Title is required.");
      return;
    }
    if (!Number.isFinite(parsedCount) || parsedCount < 1) {
      setError("Target count must be at least 1.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      await onSave({
        targetId: draft.targetId,
        title: cleanedTitle,
        targetCount: parsedCount,
      });
      onClose();
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "Could not save target",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="pf-task-form" onSubmit={(event) => void handleSubmit(event)}>
      <FormField label="Goal">
        <Input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Exercise 3 times"
          autoFocus
        />
      </FormField>
      <FormField
        label="Times per week"
        hint="How many times you want to complete this goal each week."
      >
        <Input
          type="number"
          min={1}
          value={targetCount}
          onChange={(event) => setTargetCount(event.target.value)}
        />
      </FormField>
      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}
      <div className="pf-task-form__actions">
        <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {draft.targetId ? "Save changes" : "Add target"}
        </Button>
      </div>
    </form>
  );
}

export interface WeeklyTargetDialogProps {
  open: boolean;
  draft: WeeklyTargetDraft | null;
  onClose: () => void;
  onSave: (draft: WeeklyTargetDraft) => Promise<void>;
}

export function WeeklyTargetDialog({
  open,
  draft,
  onClose,
  onSave,
}: WeeklyTargetDialogProps) {
  return (
    <Dialog
      open={open}
      title={draft?.targetId ? "Edit weekly target" : "Add weekly target"}
      onClose={onClose}
    >
      {open && draft ? (
        <WeeklyTargetForm
          key={draft.targetId ?? "new"}
          draft={draft}
          onClose={onClose}
          onSave={onSave}
        />
      ) : null}
    </Dialog>
  );
}
