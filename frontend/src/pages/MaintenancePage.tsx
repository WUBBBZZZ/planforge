import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { LoadingIndicator } from "../components/LoadingIndicator";
import {
  MaintenanceActionsDialog,
  type MaintenanceActionMode,
} from "../components/MaintenanceActionsDialog";
import { MaintenanceEditDialog } from "../components/MaintenanceEditDialog";
import { MaintenanceHistoryBoard } from "../components/MaintenanceHistoryBoard";
import {
  archiveMaintenance,
  completeMaintenance,
  fetchMaintenanceHistoryBoard,
  formatDisplayDate,
  listMaintenance,
  maintenanceNextActionLabel,
  restoreMaintenance,
  type MaintenanceHistoryBoardData,
  type MaintenanceItem,
  type MaintenanceListFilter,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type PageState =
  | { kind: "loading" }
  | {
      kind: "ready";
      items: MaintenanceItem[];
      board: MaintenanceHistoryBoardData;
    }
  | { kind: "error"; message: string };

const FILTERS: Array<{ id: MaintenanceListFilter; label: string }> = [
  { id: "overdue", label: "Overdue" },
  { id: "due_soon", label: "Due soon" },
  { id: "needs_scheduling", label: "Needs scheduling" },
  { id: "scheduled_upcoming", label: "Scheduled upcoming" },
  { id: "active", label: "Active" },
  { id: "archived", label: "Archived" },
];

export function MaintenancePage() {
  const [filter, setFilter] = useState<MaintenanceListFilter>("active");
  const [historyLimit, setHistoryLimit] = useState(10);
  const [state, setState] = useState<PageState>({ kind: "loading" });
  const [actionError, setActionError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MaintenanceItem | null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);
  const [actionsItem, setActionsItem] = useState<MaintenanceItem | null>(null);
  const [actionsMode, setActionsMode] = useState<MaintenanceActionMode>("history");

  const reload = async () => {
    try {
      const [items, board] = await Promise.all([
        listMaintenance({ filter }),
        fetchMaintenanceHistoryBoard(historyLimit),
      ]);
      setState({ kind: "ready", items, board });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load maintenance";
      setState({ kind: "error", message });
    }
  };

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listMaintenance({ filter }),
      fetchMaintenanceHistoryBoard(historyLimit),
    ])
      .then(([items, board]) => {
        if (!cancelled) {
          setState({ kind: "ready", items, board });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load maintenance";
          setState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filter, historyLimit]);

  const runAction = async (action: () => Promise<void>) => {
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed");
    }
  };

  const openActions = (
    item: MaintenanceItem,
    mode: MaintenanceActionMode = "history",
  ) => {
    setActionsItem(item);
    setActionsMode(mode);
    setActionsOpen(true);
  };

  return (
    <AppShell
      currentPath="/maintenance"
      title="Maintenance"
      actions={
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          New maintenance
        </Button>
      }
    >
      <div className="pf-schedule-toolbar">
        <div
          className="pf-schedule-filters"
          role="group"
          aria-label="Maintenance filters"
        >
          {FILTERS.map((entry) => (
            <Button
              key={entry.id}
              variant={filter === entry.id ? "secondary" : "ghost"}
              onClick={() => setFilter(entry.id)}
              aria-pressed={filter === entry.id}
            >
              {entry.label}
            </Button>
          ))}
        </div>
      </div>

      {actionError ? (
        <p className="pf-form-field__error" role="alert">
          {actionError}
        </p>
      ) : null}

      {state.kind === "loading" ? (
        <LoadingIndicator label="Loading maintenance" />
      ) : null}
      {state.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {state.message}
        </p>
      ) : null}

      {state.kind === "ready" ? (
        <>
          <MaintenanceHistoryBoard
            rows={state.board.rows}
            historyLimit={state.board.history_limit}
            onHistoryLimitChange={setHistoryLimit}
            onOpenItem={(item) => openActions(item, "history")}
          />

          <section className="pf-maintenance-sections" aria-label="Completion history">
            <h2>Completion history</h2>
            <p className="pf-muted">
              Scroll horizontally in the table above to see older records. Select an
              item below to manage scheduling, reminders, and completions.
            </p>
          </section>

          <section
            className="pf-maintenance-sections"
            aria-label="Filtered maintenance list"
          >
            <h2>Filtered items</h2>
            {state.items.length === 0 ? (
              <EmptyState
                title="No maintenance items here"
                description="Try another filter or create a maintenance definition."
              />
            ) : (
              <ul className="pf-task-list">
                {state.items.map((item) => (
                  <li key={item.id} className="pf-task-row">
                    <div className="pf-task-row__main">
                      <p className="pf-task-row__title">{item.title}</p>
                      <div className="pf-task-row__meta">
                        <Badge>{maintenanceNextActionLabel(item)}</Badge>
                        {item.category ? <Badge>{item.category}</Badge> : null}
                        {item.last_completed_date ? (
                          <Badge>
                            Last {formatDisplayDate(item.last_completed_date)}
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                    <div className="pf-task-row__actions">
                      {item.status === "active" ? (
                        <>
                          <Button
                            variant="secondary"
                            onClick={() =>
                              void runAction(async () => {
                                await completeMaintenance(item.id);
                              })
                            }
                          >
                            Mark completed
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() => openActions(item, "schedule")}
                          >
                            Schedule
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() => openActions(item, "history")}
                          >
                            Manage
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() => {
                              setEditing(item);
                              setDialogOpen(true);
                            }}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() =>
                              void runAction(async () => {
                                await archiveMaintenance(item.id);
                              })
                            }
                          >
                            Archive
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="secondary"
                          onClick={() =>
                            void runAction(async () => {
                              await restoreMaintenance(item.id);
                            })
                          }
                        >
                          Restore
                        </Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}

      <MaintenanceEditDialog
        open={dialogOpen}
        item={editing}
        onClose={() => setDialogOpen(false)}
        onSaved={() => void reload()}
      />
      <MaintenanceActionsDialog
        open={actionsOpen}
        item={actionsItem}
        initialMode={actionsMode}
        onClose={() => setActionsOpen(false)}
        onSaved={() => void reload()}
      />
    </AppShell>
  );
}
