import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { CaptureModal } from "../components/CaptureModal";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { MonthViewContent } from "../components/views/MonthViewContent";
import {
  addMonths,
  formatMonthYear,
  getSearchParam,
  leadingPaddingDays,
  setSearchParam,
} from "../lib/dates";
import { fetchMonthView, type MonthView, type PlannerItem } from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type MonthState =
  | { kind: "loading" }
  | { kind: "ready"; view: MonthView }
  | { kind: "error"; message: string };

function readMonthParam(): string | undefined {
  const value = getSearchParam("month");
  return value ?? undefined;
}

function bucketGroups(view: MonthView) {
  const calendarDays = view.days.filter((group) => group.date !== null);
  const extraBuckets = view.days.filter((group) => group.date === null);
  return { calendarDays, extraBuckets };
}

export function MonthPage() {
  const [monthParam, setMonthParam] = useState<string | undefined>(readMonthParam);
  const [monthState, setMonthState] = useState<MonthState>({ kind: "loading" });
  const [modalOpen, setModalOpen] = useState(false);

  const reloadMonth = useCallback(async (month?: string) => {
    try {
      const view = await fetchMonthView(month);
      setMonthState({ kind: "ready", view });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load month";
      setMonthState({ kind: "error", message });
    }
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchMonthView(monthParam)
      .then((view) => {
        if (!cancelled) {
          setMonthState({ kind: "ready", view });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load month";
          setMonthState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [monthParam]);

  const navigateMonth = (nextMonth: string | undefined) => {
    setMonthState({ kind: "loading" });
    setMonthParam(nextMonth);
    setSearchParam("month", nextMonth ?? null);
  };

  const periodLabel =
    monthState.kind === "ready" ? formatMonthYear(monthState.view.month) : "Loading…";

  const calendar = useMemo(() => {
    if (monthState.kind !== "ready") {
      return null;
    }

    const { calendarDays } = bucketGroups(monthState.view);
    const padding = leadingPaddingDays(
      monthState.view.month_start,
      monthState.view.week_start_day,
    );
    const cells: Array<
      { kind: "pad" } | { kind: "day"; date: string; items: PlannerItem[] }
    > = Array.from({ length: padding }, () => ({ kind: "pad" as const }));
    for (const group of calendarDays) {
      if (!group.date) {
        continue;
      }
      cells.push({ kind: "day", date: group.date, items: group.items });
    }
    while (cells.length % 7 !== 0) {
      cells.push({ kind: "pad" });
    }
    return cells;
  }, [monthState]);

  const extraBuckets =
    monthState.kind === "ready" ? bucketGroups(monthState.view).extraBuckets : [];

  return (
    <AppShell
      currentPath="/month"
      title="Month"
      actions={<Button onClick={() => setModalOpen(true)}>Capture</Button>}
    >
      {monthState.kind === "loading" ? (
        <LoadingIndicator label="Loading month view" />
      ) : null}

      {monthState.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {monthState.message}
        </p>
      ) : null}

      {monthState.kind === "ready" && calendar ? (
        <MonthViewContent
          view={monthState.view}
          periodLabel={periodLabel}
          calendar={calendar}
          extraBuckets={extraBuckets}
          onPrevious={() => navigateMonth(addMonths(monthState.view.month, -1))}
          onNext={() => navigateMonth(addMonths(monthState.view.month, 1))}
          onToday={() => navigateMonth(undefined)}
          onReload={async () => reloadMonth(monthParam)}
        />
      ) : null}

      <CaptureModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void reloadMonth(monthParam)}
      />
    </AppShell>
  );
}
