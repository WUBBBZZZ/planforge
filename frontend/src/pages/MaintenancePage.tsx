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
import { todayIsoLocal } from "../lib/dates";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type MaintenanceTab = "items" | "history";

type ItemsState =
  | { kind: "loading" }
  | { kind: "ready"; items: MaintenanceItem[] }
  | { kind: "error"; message: string };

type HistoryState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; board: MaintenanceHistoryBoardData }
  | { kind: "error"; message: string };

const FILTERS: Array<{ id: MaintenanceListFilter; label: string }> = [
  { id: "overdue", label: "Overdue" },
  { id: "due_soon", label: "Due soon" },
  { id: "needs_scheduling", label: "Needs scheduling" },
  { id: "scheduled_upcoming", label: "Scheduled upcoming" },
  { id: "active", label: "Active" },
  { id: "archived", label: "Archived" },
];

const TABS: Array<{ id: MaintenanceTab; label: string }> = [
  { id: "items", label: "Items" },
  { id: "history", label: "History" },
];

export function MaintenancePage() {
  const [activeTab, setActiveTab] = useState<MaintenanceTab>("items");
  const [filter, setFilter] = useState<MaintenanceListFilter>("active");
  const [historyLimit, setHistoryLimit] = useState(10);
  const [itemsState, setItemsState] = useState<ItemsState>({ kind: "loading" });
  const [loadedFilter, setLoadedFilter] = useState<MaintenanceListFilter | null>(null);
  const [historyState, setHistoryState] = useState<HistoryState>({ kind: "idle" });
  const [loadedHistoryLimit, setLoadedHistoryLimit] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MaintenanceItem | null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);
  const [actionsItem, setActionsItem] = useState<MaintenanceItem | null>(null);
  const [actionsMode, setActionsMode] = useState<MaintenanceActionMode>("history");

  const loadItems = async (nextFilter = filter) => {
    try {
      const items = await listMaintenance({ filter: nextFilter });
      setItemsState({ kind: "ready", items });
      setLoadedFilter(nextFilter);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load maintenance";
      setItemsState({ kind: "error", message });
      setLoadedFilter(nextFilter);
    }
  };

  const loadHistory = async (limit = historyLimit) => {
    setHistoryState({ kind: "loading" });
    try {
      const board = await fetchMaintenanceHistoryBoard(limit);
      setHistoryState({ kind: "ready", board });
      setLoadedHistoryLimit(limit);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load maintenance history";
      setHistoryState({ kind: "error", message });
      setLoadedHistoryLimit(limit);
    }
  };

  const reload = async () => {
    await Promise.all([
      loadItems(),
      activeTab === "history" ? loadHistory() : Promise.resolve(),
    ]);
  };

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    listMaintenance({ filter })
      .then((items) => {
        if (!cancelled) {
          setItemsState({ kind: "ready", items });
          setLoadedFilter(filter);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load maintenance";
          setItemsState({ kind: "error", message });
          setLoadedFilter(filter);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filter]);

  useEffect(() => {
    if (activeTab !== "history") {
      return;
    }
    let cancelled = false;
    fetchMaintenanceHistoryBoard(historyLimit)
      .then((board) => {
        if (!cancelled) {
          setHistoryState({ kind: "ready", board });
          setLoadedHistoryLimit(historyLimit);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error
              ? error.message
              : "Could not load maintenance history";
          setHistoryState({ kind: "error", message });
          setLoadedHistoryLimit(historyLimit);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [activeTab, historyLimit]);

  const displayItemsState: ItemsState =
    loadedFilter === filter ? itemsState : { kind: "loading" };
  const displayHistoryState: HistoryState =
    activeTab !== "history"
      ? historyState
      : loadedHistoryLimit === historyLimit && historyState.kind !== "idle"
        ? historyState
        : { kind: "loading" };

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
      <div className="pf-page-tabs" role="tablist" aria-label="Maintenance views">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            className="pf-page-tabs__tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`maintenance-panel-${tab.id}`}
            id={`maintenance-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {actionError ? (
        <p className="pf-form-field__error" role="alert">
          {actionError}
        </p>
      ) : null}

      {activeTab === "items" ? (
        <div
          id="maintenance-panel-items"
          role="tabpanel"
          aria-labelledby="maintenance-tab-items"
          className="pf-maintenance-panel"
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

          {displayItemsState.kind === "loading" ? (
            <LoadingIndicator label="Loading maintenance" />
          ) : null}
          {displayItemsState.kind === "error" ? (
            <p className="pf-form-field__error" role="alert">
              {displayItemsState.message}
            </p>
          ) : null}

          {displayItemsState.kind === "ready" ? (
            <section aria-label="Filtered maintenance list">
              {displayItemsState.items.length === 0 ? (
                <EmptyState
                  title="No maintenance items here"
                  description="Try another filter or create a maintenance definition."
                />
              ) : (
                <ul className="pf-task-list">
                  {displayItemsState.items.map((item) => (
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
                                  await completeMaintenance(item.id, {
                                    completed_on: todayIsoLocal(),
                                  });
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
                              onClick={() => {
                                if (
                                  window.confirm(
                                    `Delete "${item.title}"? This archives the maintenance item.`,
                                  )
                                ) {
                                  void runAction(async () => {
                                    await archiveMaintenance(item.id);
                                  });
                                }
                              }}
                            >
                              Delete
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
          ) : null}
        </div>
      ) : null}

      {activeTab === "history" ? (
        <div
          id="maintenance-panel-history"
          role="tabpanel"
          aria-labelledby="maintenance-tab-history"
          className="pf-maintenance-panel"
        >
          {displayHistoryState.kind === "loading" ? (
            <LoadingIndicator label="Loading maintenance history" />
          ) : null}
          {displayHistoryState.kind === "error" ? (
            <p className="pf-form-field__error" role="alert">
              {displayHistoryState.message}
            </p>
          ) : null}
          {displayHistoryState.kind === "ready" ? (
            <MaintenanceHistoryBoard
              rows={displayHistoryState.board.rows}
              historyLimit={displayHistoryState.board.history_limit}
              onHistoryLimitChange={setHistoryLimit}
              onOpenItem={(item) => openActions(item, "history")}
            />
          ) : null}
        </div>
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
