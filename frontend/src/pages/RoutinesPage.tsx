import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { Select } from "../components/Select";
import {
  createRoutine,
  listRoutines,
  pauseRoutine,
  resumeRoutine,
  updateRoutine,
  type Routine,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatRoutineSchedule(routine: Routine): string {
  if (routine.schedule_type === "monthly") {
    const suffix =
      routine.day_of_month === 1
        ? "st"
        : routine.day_of_month === 2
          ? "nd"
          : routine.day_of_month === 3
            ? "rd"
            : "th";
    return `Monthly on the ${routine.day_of_month}${suffix}`;
  }
  const days = routine.days_of_week.map((day) => WEEKDAY_LABELS[day]).join(", ");
  const interval =
    routine.interval_weeks === 1
      ? "Every week"
      : `Every ${routine.interval_weeks} weeks`;
  return `${interval} on ${days}`;
}

function todayIso(): string {
  const now = new Date();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

export function RoutinesPage() {
  const [routines, setRoutines] = useState<Routine[] | null>(null);
  const [title, setTitle] = useState("");
  const [scheduleType, setScheduleType] = useState<"weekly" | "monthly">("weekly");
  const [selectedDays, setSelectedDays] = useState<number[]>([4]);
  const [dayOfMonth, setDayOfMonth] = useState("1");
  const [intervalWeeks, setIntervalWeeks] = useState("1");
  const [startsOn, setStartsOn] = useState(todayIso());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setRoutines(await listRoutines());
  };

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    listRoutines()
      .then((items) => {
        if (!cancelled) {
          setRoutines(items);
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error ? loadError.message : "Could not load routines",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const resetForm = () => {
    setTitle("");
    setScheduleType("weekly");
    setSelectedDays([4]);
    setDayOfMonth("1");
    setIntervalWeeks("1");
    setStartsOn(todayIso());
    setEditingId(null);
  };

  const toggleDay = (day: number) => {
    setSelectedDays((current) =>
      current.includes(day) ? current.filter((value) => value !== day) : [...current, day].sort(),
    );
  };

  const loadRoutineForEdit = (routine: Routine) => {
    setEditingId(routine.id);
    setTitle(routine.title);
    setScheduleType(routine.schedule_type);
    setSelectedDays(routine.days_of_week);
    setDayOfMonth(String(routine.day_of_month ?? 1));
    setIntervalWeeks(String(routine.interval_weeks));
    setStartsOn(routine.starts_on ?? todayIso());
  };

  const buildPayload = () => {
    const payload = {
      title,
      schedule_type: scheduleType,
      starts_on: startsOn || todayIso(),
      interval_weeks: Number(intervalWeeks) || 1,
    };
    if (scheduleType === "weekly") {
      return {
        ...payload,
        days_of_week: selectedDays.length > 0 ? selectedDays : [4],
        day_of_month: null,
      };
    }
    return {
      ...payload,
      days_of_week: [0],
      day_of_month: Number(dayOfMonth) || 1,
    };
  };

  const handleSave = async () => {
    setError(null);
    try {
      if (editingId) {
        await updateRoutine(editingId, buildPayload());
      } else {
        await createRoutine(buildPayload());
      }
      resetForm();
      await reload();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save");
    }
  };

  const togglePause = async (routine: Routine) => {
    if (routine.status === "active") {
      await pauseRoutine(routine.id);
    } else if (routine.status === "paused") {
      await resumeRoutine(routine.id);
    }
    await reload();
  };

  return (
    <AppShell currentPath="/routines" title="Routines">
      <section className="pf-panel">
        <h2>{editingId ? "Edit routine" : "Create routine"}</h2>
        <FormField label="Title">
          <Input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Change sheets"
          />
        </FormField>

        <FormField label="Schedule type">
          <Select
            value={scheduleType}
            options={[
              { value: "weekly", label: "Weekly (e.g. every Thursday)" },
              { value: "monthly", label: "Monthly (calendar date, e.g. 1st)" },
            ]}
            onChange={(event) =>
              setScheduleType(event.target.value as "weekly" | "monthly")
            }
          />
        </FormField>

        {scheduleType === "weekly" ? (
          <>
            <FormField label="Days of week">
              <div className="pf-weekday-picker">
                {WEEKDAY_LABELS.map((label, index) => (
                  <label key={label} className="pf-weekday-picker__option">
                    <input
                      type="checkbox"
                      checked={selectedDays.includes(index)}
                      onChange={() => toggleDay(index)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </FormField>
            <FormField label="Repeat every N weeks" hint="1 = every week, 2 = every other week">
              <Input
                type="number"
                min={1}
                max={52}
                value={intervalWeeks}
                onChange={(event) => setIntervalWeeks(event.target.value)}
              />
            </FormField>
          </>
        ) : (
          <FormField label="Day of month" hint="Uses the last day when a month is shorter">
            <Input
              type="number"
              min={1}
              max={31}
              value={dayOfMonth}
              onChange={(event) => setDayOfMonth(event.target.value)}
            />
          </FormField>
        )}

        <FormField label="Starts on" hint="Occurrences are only generated from this date forward">
          <Input
            type="date"
            value={startsOn}
            onChange={(event) => setStartsOn(event.target.value)}
          />
        </FormField>

        <div className="pf-task-form__actions">
          {editingId ? (
            <Button variant="ghost" onClick={resetForm}>
              Cancel edit
            </Button>
          ) : null}
          <Button onClick={() => void handleSave()}>
            {editingId ? "Save changes" : "Create routine"}
          </Button>
        </div>
        {error ? <p className="pf-form-field__error">{error}</p> : null}
      </section>

      {routines === null ? <LoadingIndicator label="Loading routines" /> : null}
      {routines && routines.length === 0 ? (
        <EmptyState
          title="No routines yet"
          description="Create a weekly or monthly routine to generate occurrences in Week and Today."
        />
      ) : null}
      {routines && routines.length > 0 ? (
        <ul className="pf-task-list">
          {routines.map((routine) => (
            <li key={routine.id} className="pf-task-row">
              <div className="pf-task-row__main">
                <p className="pf-task-row__title">{routine.title}</p>
                <p className="pf-muted">
                  {formatRoutineSchedule(routine)}
                  {routine.starts_on ? ` · starts ${routine.starts_on}` : ""} · {routine.status}
                </p>
              </div>
              <div className="pf-task-row__actions">
                <Button variant="secondary" onClick={() => loadRoutineForEdit(routine)}>
                  Edit
                </Button>
                {routine.status !== "archived" ? (
                  <Button variant="ghost" onClick={() => void togglePause(routine)}>
                    {routine.status === "active" ? "Pause" : "Resume"}
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </AppShell>
  );
}
