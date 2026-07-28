import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import {
  archiveBacklogItem,
  listBacklog,
  promoteBacklogItem,
  type BacklogItem,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type BacklogState =
  | { kind: "loading" }
  | { kind: "ready"; items: BacklogItem[] }
  | { kind: "error"; message: string };

export function BacklogPage() {
  const [state, setState] = useState<BacklogState>({ kind: "loading" });
  const [promoteDates, setPromoteDates] = useState<Record<string, string>>({});

  const reload = useCallback(async () => {
    try {
      const items = await listBacklog();
      setState({ kind: "ready", items });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load backlog";
      setState({ kind: "error", message });
    }
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    listBacklog()
      .then((items) => {
        if (!cancelled) {
          setState({ kind: "ready", items });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load backlog";
          setState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handlePromote = async (itemId: string) => {
    const dueDate = promoteDates[itemId];
    if (!dueDate) {
      return;
    }
    await promoteBacklogItem(itemId, dueDate);
    await reload();
  };

  const handleArchive = async (itemId: string) => {
    await archiveBacklogItem(itemId);
    await reload();
  };

  return (
    <AppShell currentPath="/backlog" title="Backlog">
      {state.kind === "loading" ? <LoadingIndicator label="Loading backlog" /> : null}
      {state.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {state.message}
        </p>
      ) : null}
      {state.kind === "ready" ? (
        state.items.length === 0 ? (
          <EmptyState
            title="Backlog is empty"
            description="Capture ideas without a due date, then promote them when you are ready to schedule."
          />
        ) : (
          <ul className="pf-task-list">
            {state.items.map((item) => (
              <li key={item.id} className="pf-task-row">
                <div className="pf-task-row__main">
                  <p className="pf-task-row__title">{item.title}</p>
                  {item.notes ? <p className="pf-muted">{item.notes}</p> : null}
                </div>
                <div className="pf-task-row__actions pf-backlog-actions">
                  <Input
                    type="date"
                    aria-label={`Due date for ${item.title}`}
                    value={promoteDates[item.id] ?? ""}
                    onChange={(event) =>
                      setPromoteDates((current) => ({
                        ...current,
                        [item.id]: event.target.value,
                      }))
                    }
                  />
                  <Button
                    variant="secondary"
                    onClick={() => void handlePromote(item.id)}
                  >
                    Promote
                  </Button>
                  <Button variant="ghost" onClick={() => void handleArchive(item.id)}>
                    Archive
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )
      ) : null}
    </AppShell>
  );
}
