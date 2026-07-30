import { useCallback, useEffect, useState, type FormEvent } from "react";

import { AppShell } from "../components/AppShell";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import {
  createPackingEntry,
  createPackingList,
  deletePackingEntry,
  deletePackingList,
  fetchPackingList,
  listPackingLists,
  updatePackingEntry,
  type PackingListDetail,
  type PackingListEntry,
  type PackingListSummary,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

export function PackingListsPage() {
  const [summaries, setSummaries] = useState<PackingListSummary[] | null>(null);
  const [selectedListId, setSelectedListId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PackingListDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newListTitle, setNewListTitle] = useState("");
  const [newItemTitle, setNewItemTitle] = useState("");
  const [newQuestionTitle, setNewQuestionTitle] = useState("");
  const [creatingList, setCreatingList] = useState(false);

  const loadSummaries = useCallback(async () => {
    const lists = await listPackingLists();
    setSummaries(lists);
    setSelectedListId((current) => {
      if (current && lists.some((list) => list.id === current)) {
        return current;
      }
      return lists[0]?.id ?? null;
    });
    return lists;
  }, []);

  const loadDetail = useCallback(async (listId: string) => {
    const nextDetail = await fetchPackingList(listId);
    setDetail(nextDetail);
    return nextDetail;
  }, []);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const lists = await loadSummaries();
      const listId = selectedListId ?? lists[0]?.id ?? null;
      if (listId) {
        await loadDetail(listId);
      } else {
        setDetail(null);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load packing lists");
    }
  }, [loadDetail, loadSummaries, selectedListId]);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    loadSummaries()
      .then((lists) => {
        if (!cancelled && lists[0]) {
          return loadDetail(lists[0].id);
        }
        return undefined;
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error ? loadError.message : "Could not load packing lists",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [loadDetail, loadSummaries]);

  useEffect(() => {
    if (!selectedListId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    loadDetail(selectedListId).catch((loadError: unknown) => {
      if (!cancelled) {
        setError(
          loadError instanceof Error ? loadError.message : "Could not load packing list",
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, [loadDetail, selectedListId]);

  const runAction = async (action: () => Promise<void>) => {
    setError(null);
    try {
      await action();
      await reload();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Action failed");
    }
  };

  const handleCreateList = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const title = newListTitle.trim();
    if (!title) {
      setError("Enter a list name before creating.");
      return;
    }
    setCreatingList(true);
    setError(null);
    try {
      const created = await createPackingList({ title });
      setNewListTitle("");
      await loadSummaries();
      setSelectedListId(created.id);
      setDetail(created);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Could not create list");
    } finally {
      setCreatingList(false);
    }
  };

  const handleAddEntry = async (
    entryType: "item" | "question",
    title: string,
    clear: () => void,
  ) => {
    if (!selectedListId) {
      return;
    }
    const trimmed = title.trim();
    if (!trimmed) {
      setError(`Enter a ${entryType === "item" ? "item" : "question"} before adding.`);
      return;
    }
    await runAction(async () => {
      await createPackingEntry(selectedListId, {
        entry_type: entryType,
        title: trimmed,
      });
      clear();
    });
  };

  const items = detail?.entries.filter((entry) => entry.entry_type === "item") ?? [];
  const questions =
    detail?.entries.filter((entry) => entry.entry_type === "question") ?? [];

  return (
    <AppShell currentPath="/packing" title="Packing lists">
      {summaries === null && !error ? (
        <LoadingIndicator label="Loading packing lists" />
      ) : null}
      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}

      <section className="pf-panel pf-packing-create">
        <h2>New list</h2>
        <form className="pf-task-form" onSubmit={(event) => void handleCreateList(event)}>
          <FormField label="Trip or event name">
            <Input
              value={newListTitle}
              onChange={(event) => setNewListTitle(event.target.value)}
              placeholder="Beach weekend"
              required
            />
          </FormField>
          <div className="pf-task-form__actions">
            <Button type="submit" disabled={creatingList}>
              {creatingList ? "Creating…" : "Create list"}
            </Button>
          </div>
        </form>
      </section>

      {summaries && summaries.length > 0 ? (
        <>
          <div className="pf-page-tabs" role="tablist" aria-label="Packing lists">
            {summaries.map((summary) => (
              <button
                key={summary.id}
                type="button"
                role="tab"
                className="pf-page-tabs__tab"
                aria-selected={selectedListId === summary.id}
                onClick={() => setSelectedListId(summary.id)}
              >
                {summary.title}
              </button>
            ))}
          </div>

          {detail ? (
            <div className="pf-packing-detail">
              <header className="pf-packing-detail__header">
                <div>
                  <h2>{detail.title}</h2>
                  {detail.notes ? <p className="pf-muted">{detail.notes}</p> : null}
                </div>
                <Button
                  variant="ghost"
                  onClick={() => {
                    if (
                      window.confirm(
                        `Delete "${detail.title}" and all of its items and questions?`,
                      )
                    ) {
                      void runAction(async () => {
                        await deletePackingList(detail.id);
                        setSelectedListId(null);
                      });
                    }
                  }}
                >
                  Delete list
                </Button>
              </header>

              <section className="pf-panel pf-packing-section">
                <h3>Items to bring</h3>
                <form
                  className="pf-packing-add-row"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleAddEntry("item", newItemTitle, () => setNewItemTitle(""));
                  }}
                >
                  <Input
                    value={newItemTitle}
                    onChange={(event) => setNewItemTitle(event.target.value)}
                    placeholder="Sunscreen, charger, passport…"
                    aria-label="New packing item"
                  />
                  <Button type="submit" variant="secondary">
                    Add item
                  </Button>
                </form>
                {items.length === 0 ? (
                  <p className="pf-muted">No items yet.</p>
                ) : (
                  <ul className="pf-packing-entry-list">
                    {items.map((entry) => (
                      <PackingItemRow
                        key={entry.id}
                        entry={entry}
                        onToggle={(checked) =>
                          void runAction(async () => {
                            await updatePackingEntry(entry.id, { is_checked: checked });
                          })
                        }
                        onDelete={() =>
                          void runAction(async () => {
                            await deletePackingEntry(entry.id);
                          })
                        }
                      />
                    ))}
                  </ul>
                )}
              </section>

              <section className="pf-panel pf-packing-section">
                <h3>Trip questions</h3>
                <p className="pf-muted">
                  Answer planning questions like whether you need formal clothes or swim gear.
                </p>
                <form
                  className="pf-packing-add-row"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleAddEntry("question", newQuestionTitle, () =>
                      setNewQuestionTitle(""),
                    );
                  }}
                >
                  <Input
                    value={newQuestionTitle}
                    onChange={(event) => setNewQuestionTitle(event.target.value)}
                    placeholder="Do I need swim trunks?"
                    aria-label="New trip question"
                  />
                  <Button type="submit" variant="secondary">
                    Add question
                  </Button>
                </form>
                {questions.length === 0 ? (
                  <p className="pf-muted">No questions yet.</p>
                ) : (
                  <ul className="pf-packing-entry-list">
                    {questions.map((entry) => (
                      <PackingQuestionRow
                        key={entry.id}
                        entry={entry}
                        onAnswer={(answer) =>
                          void runAction(async () => {
                            await updatePackingEntry(entry.id, { answer });
                          })
                        }
                        onClear={() =>
                          void runAction(async () => {
                            await updatePackingEntry(entry.id, { clear_answer: true });
                          })
                        }
                        onDelete={() =>
                          void runAction(async () => {
                            await deletePackingEntry(entry.id);
                          })
                        }
                      />
                    ))}
                  </ul>
                )}
              </section>
            </div>
          ) : null}
        </>
      ) : summaries ? (
        <EmptyState
          title="No packing lists yet"
          description="Create a list for your next trip, then add items to pack and questions to answer."
        />
      ) : null}
    </AppShell>
  );
}

function PackingItemRow({
  entry,
  onToggle,
  onDelete,
}: {
  entry: PackingListEntry;
  onToggle: (checked: boolean) => void;
  onDelete: () => void;
}) {
  return (
    <li className="pf-packing-entry">
      <label className="pf-packing-entry__label">
        <input
          type="checkbox"
          checked={entry.is_checked}
          onChange={(event) => onToggle(event.target.checked)}
        />
        <span className={entry.is_checked ? "pf-packing-entry__title--done" : undefined}>
          {entry.title}
        </span>
      </label>
      <Button variant="ghost" onClick={onDelete}>
        Remove
      </Button>
    </li>
  );
}

function PackingQuestionRow({
  entry,
  onAnswer,
  onClear,
  onDelete,
}: {
  entry: PackingListEntry;
  onAnswer: (answer: "yes" | "no") => void;
  onClear: () => void;
  onDelete: () => void;
}) {
  return (
    <li className="pf-packing-entry pf-packing-entry--question">
      <div className="pf-packing-entry__question">
        <p className="pf-packing-entry__question-text">{entry.title}</p>
        {entry.answer ? (
          <Badge tone={entry.answer === "yes" ? "success" : "neutral"}>
            {entry.answer === "yes" ? "Yes" : "No"}
          </Badge>
        ) : (
          <Badge>Unanswered</Badge>
        )}
      </div>
      <div className="pf-packing-entry__actions">
        <Button
          variant={entry.answer === "yes" ? "secondary" : "ghost"}
          onClick={() => onAnswer("yes")}
        >
          Yes
        </Button>
        <Button
          variant={entry.answer === "no" ? "secondary" : "ghost"}
          onClick={() => onAnswer("no")}
        >
          No
        </Button>
        {entry.answer ? (
          <Button variant="ghost" onClick={onClear}>
            Clear
          </Button>
        ) : null}
        <Button variant="ghost" onClick={onDelete}>
          Remove
        </Button>
      </div>
    </li>
  );
}
