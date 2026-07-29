import { useState } from "react";

import {
  archiveAppointment,
  cancelAppointment,
  cancelTask,
  completeAppointment,
  completeMaintenance,
  completeOccurrence,
  completeTask,
  formatDisplayDate,
  formatTimeRange,
  getAppointment,
  itemKindLabel,
  moveTaskToBacklog,
  reopenTask,
  skipOccurrence,
  type Appointment,
  type PlannerItem,
} from "../lib/tasks";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { AppointmentEditDialog } from "./AppointmentEditDialog";
import { TaskEditDialog } from "./TaskEditDialog";

export interface PlannerItemRowProps {
  item: PlannerItem;
  onChanged: () => Promise<void>;
  compact?: boolean;
}

function confirmAction(message: string): boolean {
  return window.confirm(message);
}

function occurrenceRoleLabel(role: PlannerItem["occurrence_role"]): string | null {
  switch (role) {
    case "overdue":
      return "Overdue";
    case "current":
      return "Current";
    case "next":
      return "Next";
    default:
      return null;
  }
}

export function PlannerItemRow({
  item,
  onChanged,
  compact = false,
}: PlannerItemRowProps) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [appointmentEdit, setAppointmentEdit] = useState<Appointment | null>(null);

  const runAction = async (actionKey: string, action: () => Promise<void>) => {
    setBusyAction(actionKey);
    setActionError(null);
    try {
      await action();
      await onChanged();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed");
    } finally {
      setBusyAction(null);
    }
  };

  const handleMoveToBacklog = async () => {
    if (
      !confirmAction(
        "Move this task to the backlog? It will be removed from your schedule.",
      )
    ) {
      return;
    }
    await runAction("move-to-backlog", async () => {
      await moveTaskToBacklog(item.item_id);
    });
  };

  const handleCancelTask = async () => {
    if (!confirmAction("Cancel this task?")) {
      return;
    }
    await runAction("cancel", async () => {
      await cancelTask(item.item_id);
    });
  };

  const openAppointmentEdit = async () => {
    setBusyAction("edit");
    setActionError(null);
    try {
      const appointment = await getAppointment(item.item_id);
      setAppointmentEdit(appointment);
      setEditOpen(true);
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "Could not load appointment",
      );
    } finally {
      setBusyAction(null);
    }
  };

  const editTask = {
    id: item.item_id,
    title: item.title,
    notes: item.notes ?? null,
    due_date: item.due_date,
  };

  return (
    <>
      <li
        className={
          compact
            ? `pf-task-row pf-task-row--compact${item.is_completed ? " pf-task-row--completed" : ""}`
            : `pf-task-row${item.is_completed ? " pf-task-row--completed" : ""}`
        }
      >
        <div className="pf-task-row__main">
          <p className="pf-task-row__title">{item.title}</p>
          <div className="pf-task-row__meta">
            {item.is_completed ? <Badge tone="success">Completed</Badge> : null}
            {item.kind === "occurrence" && occurrenceRoleLabel(item.occurrence_role) ? (
              <Badge tone={item.occurrence_role === "overdue" ? "danger" : "neutral"}>
                {occurrenceRoleLabel(item.occurrence_role)}
              </Badge>
            ) : null}
            <Badge tone={item.is_overdue ? "danger" : "neutral"}>
              {itemKindLabel(item.kind)}
            </Badge>
            {!compact && item.due_date ? (
              <Badge tone={item.is_overdue ? "danger" : "neutral"}>
                {item.is_overdue ? "Overdue · " : ""}
                {formatDisplayDate(item.due_date)}
              </Badge>
            ) : null}
            {compact && item.is_overdue ? <Badge tone="danger">Overdue</Badge> : null}
            {!compact && item.starts_at && item.ends_at ? (
              <Badge>{formatTimeRange(item.starts_at, item.ends_at)}</Badge>
            ) : null}
            {item.is_all_day ? <Badge>All day</Badge> : null}
            {item.location ? <Badge>{item.location}</Badge> : null}
          </div>
          {actionError ? (
            <p className="pf-form-field__error" role="alert">
              {actionError}
            </p>
          ) : null}
        </div>
        <div
          className={
            compact
              ? "pf-task-row__actions pf-task-row__actions--compact"
              : "pf-task-row__actions"
          }
        >
          {item.kind === "task" && item.is_completed ? (
            <Button
              variant="secondary"
              disabled={busyAction !== null}
              onClick={() =>
                void runAction("reopen", async () => {
                  await reopenTask(item.item_id);
                })
              }
            >
              {busyAction === "reopen" ? "Reopening…" : "Reopen"}
            </Button>
          ) : null}
          {item.kind === "task" && !item.is_completed ? (
            <>
              <Button
                variant="secondary"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("complete", async () => {
                    await completeTask(item.item_id);
                  })
                }
              >
                {busyAction === "complete" ? "Completing…" : "Complete"}
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() => void handleCancelTask()}
              >
                {busyAction === "cancel" ? "Cancelling…" : "Cancel"}
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() => setEditOpen(true)}
              >
                Edit
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() => void handleMoveToBacklog()}
              >
                {busyAction === "move-to-backlog" ? "Moving…" : "Move to backlog"}
              </Button>
            </>
          ) : null}
          {item.kind === "occurrence" && !item.is_completed ? (
            <>
              <Button
                variant="secondary"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("complete", async () => {
                    await completeOccurrence(item.item_id);
                  })
                }
              >
                Complete
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("skip", async () => {
                    await skipOccurrence(item.item_id);
                  })
                }
              >
                Skip
              </Button>
            </>
          ) : null}
          {item.kind === "appointment" && !item.is_completed ? (
            <>
              <Button
                variant="secondary"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("complete", async () => {
                    await completeAppointment(item.item_id);
                  })
                }
              >
                Complete
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("cancel", async () => {
                    await cancelAppointment(item.item_id);
                  })
                }
              >
                Cancel
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() => void openAppointmentEdit()}
              >
                {busyAction === "edit" ? "Loading…" : "Edit"}
              </Button>
              <Button
                variant="ghost"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction("archive", async () => {
                    await archiveAppointment(item.item_id);
                  })
                }
              >
                Archive
              </Button>
            </>
          ) : null}
          {item.kind === "maintenance" && !item.is_completed ? (
            <Button
              variant="secondary"
              disabled={busyAction !== null}
              onClick={() =>
                void runAction("complete", async () => {
                  await completeMaintenance(item.item_id);
                })
              }
            >
              Complete
            </Button>
          ) : null}
        </div>
      </li>
      {item.kind === "task" && !item.is_completed ? (
        <TaskEditDialog
          open={editOpen}
          task={editTask}
          onClose={() => setEditOpen(false)}
          onSaved={() => void onChanged()}
          onMoveToBacklog={() => {
            setEditOpen(false);
            void handleMoveToBacklog();
          }}
        />
      ) : null}
      {item.kind === "appointment" ? (
        <AppointmentEditDialog
          open={editOpen}
          appointment={appointmentEdit}
          onClose={() => {
            setEditOpen(false);
            setAppointmentEdit(null);
          }}
          onSaved={() => void onChanged()}
        />
      ) : null}
    </>
  );
}
