import { useCallback, useEffect, useState } from "react";



import { AppShell } from "../components/AppShell";

import { Button } from "../components/Button";

import { CaptureModal } from "../components/CaptureModal";

import { LoadingIndicator } from "../components/LoadingIndicator";

import { WeekViewContent } from "../components/views/WeekViewContent";

import { addDays, getSearchParam, setSearchParam } from "../lib/dates";

import {

  createWeeklyTarget,

  deleteWeeklyTarget,

  fetchWeekView,

  formatDisplayDate,

  logWeeklyTargetProgress,

  updateWeeklyTarget,

  type WeekView,

} from "../lib/tasks";

import type { WeeklyTargetDraft } from "../components/WeeklyTargetDialog";

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



  const loadWeek = useCallback(async (weekStart?: string) => {

    setWeekState({ kind: "loading" });

    try {

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

    void loadWeek(weekStartParam);

  }, [loadWeek, weekStartParam]);



  const navigateWeek = (nextWeekStart: string | undefined) => {

    setWeekStartParam(nextWeekStart);

    setSearchParam("week_start", nextWeekStart ?? null);

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



      {weekState.kind === "ready" ? (

        <WeekViewContent

          view={weekState.view}

          periodLabel={periodLabel}

          onPrevious={() => navigateWeek(addDays(weekState.view.week_start, -7))}

          onNext={() => navigateWeek(addDays(weekState.view.week_start, 7))}

          onToday={() => navigateWeek(undefined)}

          onReload={async () => loadWeek(weekStartParam)}

          onLogTarget={async (targetId) => {

            await logWeeklyTargetProgress(targetId);

            await loadWeek(weekStartParam);

          }}

          onSaveTarget={async (draft: WeeklyTargetDraft) => {

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

            await loadWeek(weekStartParam);

          }}

          onDeleteTarget={async (targetId) => {

            await deleteWeeklyTarget(targetId);

            await loadWeek(weekStartParam);

          }}

        />

      ) : null}



      <CaptureModal

        open={modalOpen}

        onClose={() => setModalOpen(false)}

        onCreated={() => void loadWeek(weekStartParam)}

      />

    </AppShell>

  );

}
