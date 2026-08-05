import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { CaptureModal } from "../components/CaptureModal";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { PeriodNav } from "../components/PeriodNav";
import { TodayViewContent } from "../components/views/TodayViewContent";
import { addDays, getSearchParam, setSearchParam, todayIsoLocal } from "../lib/dates";
import {
  fetchTodayView,
  formatDisplayDate,
  syncRoutineOccurrences,
  type TodayView,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type TodayState =
  | { kind: "loading" }
  | { kind: "ready"; view: TodayView }
  | { kind: "error"; message: string };

function readDateParam(): string | undefined {
  const value = getSearchParam("date");
  return value ?? undefined;
}

export function TodayPage() {
  const [dateParam, setDateParam] = useState<string | undefined>(readDateParam);
  const [todayState, setTodayState] = useState<TodayState>({ kind: "loading" });
  const [modalOpen, setModalOpen] = useState(false);

  const reloadToday = useCallback(async (date?: string) => {
    try {
      await syncRoutineOccurrences();
      const view = await fetchTodayView(date);
      setTodayState({ kind: "ready", view });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load day";
      setTodayState({ kind: "error", message });
    }
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;

    syncRoutineOccurrences()
      .then(() => fetchTodayView(dateParam))
      .then((view) => {
        if (!cancelled) {
          setTodayState({ kind: "ready", view });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Could not load day";
          setTodayState({ kind: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [dateParam]);

  const navigateDay = (nextDate: string | undefined) => {
    setTodayState({ kind: "loading" });
    setDateParam(nextDate);
    setSearchParam("date", nextDate ?? null);
  };

  const periodLabel =
    todayState.kind === "ready"
      ? formatDisplayDate(todayState.view.reference_date)
      : "Loading…";

  const isTodaySelected =
    todayState.kind === "ready" && todayState.view.reference_date === todayIsoLocal();

  return (
    <AppShell
      currentPath="/today"
      title={isTodaySelected ? "Today" : "Day"}
      onCaptureCreated={() => void reloadToday(dateParam)}
      actions={<Button onClick={() => setModalOpen(true)}>Capture</Button>}
    >
      {todayState.kind === "loading" ? (
        <LoadingIndicator label="Loading day view" />
      ) : null}

      {todayState.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {todayState.message}
        </p>
      ) : null}

      {todayState.kind === "ready" ? (
        <>
          <PeriodNav
            label={periodLabel}
            previousLabel="Previous day"
            nextLabel="Next day"
            todayLabel="Today"
            onPrevious={() => navigateDay(addDays(todayState.view.reference_date, -1))}
            onNext={() => navigateDay(addDays(todayState.view.reference_date, 1))}
            onToday={() => navigateDay(undefined)}
          />
          <TodayViewContent
            view={todayState.view}
            onReload={async () => reloadToday(dateParam)}
          />
        </>
      ) : null}

      <CaptureModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void reloadToday(dateParam)}
        defaultDueDate={
          todayState.kind === "ready" ? todayState.view.reference_date : undefined
        }
      />
    </AppShell>
  );
}
