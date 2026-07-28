import { useState } from "react";

import {
  cancelAppointment,
  cancelTask,
  completeAppointment,
  completeMaintenance,
  completeOccurrence,
  completeTask,
  formatDisplayDate,
  formatTimeRange,
  itemKindLabel,
  skipOccurrence,
  type PlannerItem,
} from "../lib/tasks";
import { Badge } from "./Badge";
import { Button } from "./Button";

export interface PlannerItemRowProps {
  item: PlannerItem;
  onChanged: () => Promise<void>;
  compact?: boolean;
}

export function PlannerItemRow({
  item,
  onChanged,
  compact = false,
}: PlannerItemRowProps) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

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

  return (
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
        {item.is_completed ? null : (
          <>
            {item.kind === "task" ? (
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
                  onClick={() =>
                    void runAction("cancel", async () => {
                      await cancelTask(item.item_id);
                    })
                  }
                >
                  {busyAction === "cancel" ? "Cancelling…" : "Cancel"}
                </Button>
              </>
            ) : null}
            {item.kind === "occurrence" ? (
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
            {item.kind === "appointment" ? (
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
              </>
            ) : null}
            {item.kind === "maintenance" ? (
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
          </>
        )}
      </div>
    </li>
  );
}
