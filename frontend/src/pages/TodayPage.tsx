import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { CaptureModal } from "../components/CaptureModal";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { TodayViewContent } from "../components/views/TodayViewContent";
import { fetchTodayView, syncRoutineOccurrences, type TodayView } from "../lib/tasks";
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
      await syncRoutineOccurrences();
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

    syncRoutineOccurrences()
      .then(() => fetchTodayView())
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

  return (
    <AppShell
      currentPath="/today"
      title="Today"
      actions={<Button onClick={() => setModalOpen(true)}>Capture</Button>}
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
        <TodayViewContent view={todayState.view} onReload={reloadToday} />
      ) : null}

      <CaptureModal
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
