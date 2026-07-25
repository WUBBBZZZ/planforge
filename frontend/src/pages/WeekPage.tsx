import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { TaskModal } from "../components/TaskModal";
import { TaskRow } from "../components/TaskRow";
import {
  cancelTask,
  completeTask,
  fetchWeekView,
  formatDisplayDate,
  type WeekView,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type WeekState =
  | { kind: "loading" }
  | { kind: "ready"; view: WeekView }
  | { kind: "error"; message: string };

export function WeekPage() {
  const [weekState, setWeekState] = useState<WeekState>({ kind: "loading" });
  const [modalOpen, setModalOpen] = useState(false);

  const reloadWeek = useCallback(async () => {
    try {
      const view = await fetchWeekView();
      setWeekState({ kind: "ready", view });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load week";
      setWeekState({ kind: "error", message });
    }
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetchWeekView()
      .then((view) => {
        if (!cancelled) {
          setWeekState({ kind: "ready", view });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load week";
          setWeekState({ kind: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleComplete = async (taskId: string) => {
    await completeTask(taskId);
    await reloadWeek();
  };

  const handleCancel = async (taskId: string) => {
    await cancelTask(taskId);
    await reloadWeek();
  };

  return (
    <AppShell
      currentPath="/week"
      title="Week"
      actions={<Button onClick={() => setModalOpen(true)}>Add task</Button>}
    >
      {weekState.kind === "loading" ? (
        <LoadingIndicator label="Loading week view" />
      ) : null}

      {weekState.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {weekState.message}
        </p>
      ) : null}

      {weekState.kind === "ready" ? (
        <div className="pf-week-view">
          <p className="pf-muted">
            {formatDisplayDate(weekState.view.week_start)} –{" "}
            {formatDisplayDate(weekState.view.week_end)}
          </p>

          {weekState.view.days.every((group) => group.tasks.length === 0) ? (
            <EmptyState
              title="No tasks this week"
              description="Add a fabricated demo task to see it grouped by due date."
            />
          ) : (
            weekState.view.days.map((group) => (
              <section
                key={group.date ?? "unscheduled"}
                className="pf-week-day"
                aria-labelledby={`week-day-${group.date ?? "unscheduled"}`}
              >
                <h2 id={`week-day-${group.date ?? "unscheduled"}`}>
                  {group.date ? formatDisplayDate(group.date) : "Unscheduled"}
                </h2>
                {group.tasks.length === 0 ? (
                  <p className="pf-muted">No tasks</p>
                ) : (
                  <ul className="pf-task-list">
                    {group.tasks.map((task) => (
                      <TaskRow
                        key={task.task_id}
                        taskId={task.task_id}
                        title={task.title}
                        dueDate={task.due_date}
                        isOverdue={task.is_overdue}
                        onComplete={handleComplete}
                        onCancel={handleCancel}
                      />
                    ))}
                  </ul>
                )}
              </section>
            ))
          )}
        </div>
      ) : null}

      <TaskModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void reloadWeek()}
      />
    </AppShell>
  );
}
