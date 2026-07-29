import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { CaptureModal } from "../components/CaptureModal";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { WeekViewContent } from "../components/views/WeekViewContent";
import type { WeeklyTargetDraft } from "../components/WeeklyTargetDialog";
import { addDays, getSearchParam, setSearchParam } from "../lib/dates";
import {
  createWeeklyTarget,
  deleteWeeklyTarget,
  fetchWeekView,
  formatDisplayDate,
  logWeeklyTargetProgress,
  syncRoutineOccurrences,
  updateWeeklyTarget,
  type WeekView,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type WeekState =
  | { kind: "loading" }
  | { kind: "ready"; view: WeekView }
  | { kind: "error"; message: string };

function readWeekStartParam(): string | undefined {
  const value = getSearchParam("week_start");
  return value ?? undefined;
}

export function WeekPage() {
  const [weekStartParam, setWeekStartParam] = useState<string | undefined>(
    readWeekStartParam,
  );
  const [weekState, setWeekState] = useState<WeekState>({ kind: "loading" });
  const [modalOpen, setModalOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const reloadWeek = useCallback(async (weekStart?: string) => {
    try {
      await syncRoutineOccurrences();
      const view = await fetchWeekView(weekStart);
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
    syncRoutineOccurrences()
      .then(() => fetchWeekView(weekStartParam))
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
  }, [weekStartParam]);

  const navigateWeek = (nextWeekStart: string | undefined) => {
    setWeekState({ kind: "loading" });
    setWeekStartParam(nextWeekStart);
    setSearchParam("week_start", nextWeekStart ?? null);
  };

  const runTargetAction = async (action: () => Promise<void>) => {
    setActionError(null);
    try {
      await action();
      await reloadWeek(weekStartParam);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed");
    }
  };

  const periodLabel =
    weekState.kind === "ready"
      ? `${formatDisplayDate(weekState.view.week_start)} – ${formatDisplayDate(weekState.view.week_end)}`
      : "Loading…";

  return (
    <AppShell
      currentPath="/week"
      title="Week"
      actions={<Button onClick={() => setModalOpen(true)}>Capture</Button>}
    >
      {weekState.kind === "loading" ? (
        <LoadingIndicator label="Loading week view" />
      ) : null}

      {weekState.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {weekState.message}
        </p>
      ) : null}

      {actionError ? (
        <p className="pf-form-field__error" role="alert">
          {actionError}
        </p>
      ) : null}

      {weekState.kind === "ready" ? (
        <WeekViewContent
          view={weekState.view}
          periodLabel={periodLabel}
          onPrevious={() => navigateWeek(addDays(weekState.view.week_start, -7))}
          onNext={() => navigateWeek(addDays(weekState.view.week_start, 7))}
          onToday={() => navigateWeek(undefined)}
          onReload={async () => reloadWeek(weekStartParam)}
          onLogTarget={async (targetId) => {
            await runTargetAction(async () => {
              await logWeeklyTargetProgress(targetId);
            });
          }}
          onSaveTarget={async (draft: WeeklyTargetDraft) => {
            await runTargetAction(async () => {
              if (draft.targetId) {
                await updateWeeklyTarget(draft.targetId, {
                  title: draft.title,
                  target_count: draft.targetCount,
                });
              } else {
                await createWeeklyTarget({
                  title: draft.title,
                  target_count: draft.targetCount,
                });
              }
            });
          }}
          onDeleteTarget={async (targetId) => {
            await runTargetAction(async () => {
              await deleteWeeklyTarget(targetId);
            });
          }}
        />
      ) : null}

      <CaptureModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void reloadWeek(weekStartParam)}
      />
    </AppShell>
  );
}
