import { useState } from "react";

import { Badge } from "./Badge";
import { Button } from "./Button";
import { formatDisplayDate } from "../lib/tasks";

export interface TaskRowProps {
  taskId: string;
  title: string;
  dueDate: string | null;
  isOverdue?: boolean;
  onComplete: (taskId: string) => Promise<void>;
  onCancel: (taskId: string) => Promise<void>;
}

export function TaskRow({
  taskId,
  title,
  dueDate,
  isOverdue = false,
  onComplete,
  onCancel,
}: TaskRowProps) {
  const [busyAction, setBusyAction] = useState<"complete" | "cancel" | null>(null);

  const runAction = async (action: "complete" | "cancel") => {
    setBusyAction(action);
    try {
      if (action === "complete") {
        await onComplete(taskId);
      } else {
        await onCancel(taskId);
      }
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <li className="pf-task-row">
      <div className="pf-task-row__main">
        <p className="pf-task-row__title">{title}</p>
        {dueDate ? (
          <Badge tone={isOverdue ? "danger" : "neutral"}>
            {isOverdue ? "Overdue · " : ""}
            {formatDisplayDate(dueDate)}
          </Badge>
        ) : (
          <Badge>Unscheduled</Badge>
        )}
      </div>
      <div className="pf-task-row__actions">
        <Button
          variant="secondary"
          disabled={busyAction !== null}
          onClick={() => void runAction("complete")}
        >
          {busyAction === "complete" ? "Completing…" : "Complete"}
        </Button>
        <Button
          variant="ghost"
          disabled={busyAction !== null}
          onClick={() => void runAction("cancel")}
        >
          {busyAction === "cancel" ? "Cancelling…" : "Cancel"}
        </Button>
      </div>
    </li>
  );
}
