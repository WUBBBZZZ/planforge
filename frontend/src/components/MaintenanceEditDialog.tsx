import { useState, type FormEvent } from "react";

import {
  createMaintenance,
  updateMaintenance,
  type MaintenanceItem,
} from "../lib/tasks";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";
import { Input } from "./Input";
import { Select } from "./Select";
import { Textarea } from "./Textarea";

export interface MaintenanceEditDialogProps {
  open: boolean;
  item: MaintenanceItem | null;
  onClose: () => void;
  onSaved: () => void;
}

const INTERVAL_OPTIONS = [
  { value: "days", label: "Days" },
  { value: "weeks", label: "Weeks" },
  { value: "months", label: "Months" },
  { value: "years", label: "Years" },
  { value: "manual", label: "Manual scheduling" },
];

function MaintenanceForm({
  item,
  onClose,
  onSaved,
}: {
  item: MaintenanceItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = item != null;
  const [title, setTitle] = useState(item?.title ?? "");
  const [category, setCategory] = useState(item?.category ?? "");
  const [notes, setNotes] = useState(item?.notes ?? "");
  const [intervalUnit, setIntervalUnit] = useState<MaintenanceItem["interval_unit"]>(
    item?.interval_unit ?? "months",
  );
  const [intervalValue, setIntervalValue] = useState(String(item?.interval_value ?? 6));
  const [leadTimeDays, setLeadTimeDays] = useState(String(item?.lead_time_days ?? 30));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        title,
        category: category.trim() ? category : null,
        notes: notes.trim() ? notes : null,
        interval_unit: intervalUnit,
        interval_value: intervalUnit === "manual" ? null : Number(intervalValue || "1"),
        lead_time_days: Number(leadTimeDays || "30"),
      };
      if (isEdit && item) {
        await updateMaintenance(item.id, payload);
      } else {
        await createMaintenance(payload);
      }
      onSaved();
      onClose();
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Could not save maintenance",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="pf-task-form" onSubmit={(event) => void handleSubmit(event)}>
      <FormField label="Name">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          autoFocus
        />
      </FormField>
      <FormField label="Category">
        <Input value={category} onChange={(e) => setCategory(e.target.value)} />
      </FormField>
      <FormField label="Notes">
        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
      </FormField>
      <FormField label="Typical interval">
        <Select
          value={intervalUnit}
          onChange={(e) =>
            setIntervalUnit(e.target.value as MaintenanceItem["interval_unit"])
          }
          options={INTERVAL_OPTIONS}
        />
      </FormField>
      {intervalUnit !== "manual" ? (
        <FormField label="Every">
          <Input
            type="number"
            min={1}
            value={intervalValue}
            onChange={(e) => setIntervalValue(e.target.value)}
            required
          />
        </FormField>
      ) : null}
      <FormField label="Schedule by / show in Upcoming (days before due)">
        <Input
          type="number"
          min={0}
          value={leadTimeDays}
          onChange={(e) => setLeadTimeDays(e.target.value)}
        />
      </FormField>
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
          {submitting ? "Saving…" : isEdit ? "Save changes" : "Create maintenance"}
        </Button>
      </div>
    </form>
  );
}

export function MaintenanceEditDialog({
  open,
  item,
  onClose,
  onSaved,
}: MaintenanceEditDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={item ? "Edit maintenance" : "Create maintenance"}
    >
      {open ? (
        <MaintenanceForm
          key={item?.id ?? "new"}
          item={item}
          onClose={onClose}
          onSaved={onSaved}
        />
      ) : null}
    </Dialog>
  );
}
