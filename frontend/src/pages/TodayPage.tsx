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
  fetchTodayView,
  formatDisplayDate,
  type TodayView,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type TodayState =
  | { kind: "loading" }
  | { kind: "ready"; view: TodayView }
  | { kind: "error"; message: string };

export function TodayPage() {
  const [todayState, setTodayState] = useState<TodayState>({ kind: "loading" });
  const [modalOpen, setModalOpen] = useState(false);

  const reloadToday = useCallback(async () => {
    try {
      const view = await fetchTodayView();
      setTodayState({ kind: "ready", view });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load today";
      setTodayState({ kind: "error", message });
    }
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetchTodayView()
      .then((view) => {
        if (!cancelled) {
          setTodayState({ kind: "ready", view });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load today";
          setTodayState({ kind: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleComplete = async (taskId: string) => {
    await completeTask(taskId);
    await reloadToday();
  };

  const handleCancel = async (taskId: string) => {
    await cancelTask(taskId);
    await reloadToday();
  };

  const overdueTasks =
    todayState.kind === "ready"
      ? todayState.view.tasks.filter((task) => task.is_overdue)
      : [];
  const dueTodayTasks =
    todayState.kind === "ready"
      ? todayState.view.tasks.filter((task) => !task.is_overdue)
      : [];

  return (
    <AppShell
      currentPath="/today"
      title="Today"
      actions={<Button onClick={() => setModalOpen(true)}>Add task</Button>}
    >
      {todayState.kind === "loading" ? (
        <LoadingIndicator label="Loading today view" />
      ) : null}

      {todayState.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {todayState.message}
        </p>
      ) : null}

      {todayState.kind === "ready" ? (
        <div className="pf-today-view">
          <p className="pf-muted">{formatDisplayDate(todayState.view.reference_date)}</p>

          {todayState.view.tasks.length === 0 ? (
            <EmptyState
              title="Nothing due today"
              description="Tasks with a due date of today or overdue reminders appear here."
            />
          ) : (
            <>
              {overdueTasks.length > 0 ? (
                <section className="pf-today-section" aria-labelledby="today-overdue">
                  <h2 id="today-overdue">Overdue</h2>
                  <ul className="pf-task-list">
                    {overdueTasks.map((task) => (
                      <TaskRow
                        key={task.task_id}
                        taskId={task.task_id}
                        title={task.title}
                        dueDate={task.due_date}
                        isOverdue
                        onComplete={handleComplete}
                        onCancel={handleCancel}
                      />
                    ))}
                  </ul>
                </section>
              ) : null}

              {dueTodayTasks.length > 0 ? (
                <section className="pf-today-section" aria-labelledby="today-due">
                  <h2 id="today-due">Due today</h2>
                  <ul className="pf-task-list">
                    {dueTodayTasks.map((task) => (
                      <TaskRow
                        key={task.task_id}
                        taskId={task.task_id}
                        title={task.title}
                        dueDate={task.due_date}
                        onComplete={handleComplete}
                        onCancel={handleCancel}
                      />
                    ))}
                  </ul>
                </section>
              ) : null}
            </>
          )}
        </div>
      ) : null}

      <TaskModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void reloadToday()}
        defaultDueDate={
          todayState.kind === "ready" ? todayState.view.reference_date : undefined
        }
      />
    </AppShell>
  );
}
