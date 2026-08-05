import { useEffect, useState, type FormEvent } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { Textarea } from "../components/Textarea";
import {
  createBacklogItem,
  deleteBacklogItem,
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
  const [actionError, setActionError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  const reload = async () => {
    try {
      const items = await listBacklog();
      setState({ kind: "ready", items });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load backlog";
      setState({ kind: "error", message });
    }
  };

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

  const runAction = async (action: () => Promise<void>) => {
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed");
    }
  };

  const handlePromote = async (itemId: string) => {
    const dueDate = promoteDates[itemId];
    if (!dueDate) {
      setActionError("Choose a due date before promoting.");
      return;
    }
    await runAction(async () => {
      await promoteBacklogItem(itemId, dueDate);
    });
  };

  const handleDelete = async (itemId: string) => {
    if (!window.confirm("Delete this backlog item permanently?")) {
      return;
    }
    await runAction(async () => {
      await deleteBacklogItem(itemId);
    });
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setActionError("Enter a title before adding to the backlog.");
      return;
    }

    setCreating(true);
    setActionError(null);
    try {
      await createBacklogItem({
        title: trimmedTitle,
        notes: notes.trim() ? notes.trim() : null,
      });
      setTitle("");
      setNotes("");
      await reload();
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "Could not add backlog item",
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell currentPath="/backlog" title="Backlog">
      <section className="pf-panel pf-backlog-capture">
        <h2>Add to backlog</h2>
        <form className="pf-task-form" onSubmit={(event) => void handleCreate(event)}>
          <FormField label="Title">
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Something to do later"
              required
            />
          </FormField>
          <FormField label="Notes">
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Optional details"
              rows={2}
            />
          </FormField>
          <div className="pf-task-form__actions">
            <Button type="submit" disabled={creating}>
              {creating ? "Adding…" : "Add to backlog"}
            </Button>
          </div>
        </form>
      </section>

      {state.kind === "loading" ? <LoadingIndicator label="Loading backlog" /> : null}
      {state.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {state.message}
        </p>
      ) : null}
      {actionError ? (
        <p className="pf-form-field__error" role="alert">
          {actionError}
        </p>
      ) : null}
      {state.kind === "ready" ? (
        state.items.length === 0 ? (
          <EmptyState
            title="Backlog is empty"
            description="Use the form above to capture ideas without a due date, then promote them when you are ready to schedule."
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
                  <Button variant="ghost" onClick={() => void handleDelete(item.id)}>
                    Delete
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
