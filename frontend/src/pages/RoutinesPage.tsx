import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { Select } from "../components/Select";
import {
  createRoutine,
  createRoutineGroup,
  deleteRoutineGroup,
  fetchRoutineGroupBoard,
  fetchTodayView,
  moveRoutineToGroup,
  pauseRoutine,
  reorderRoutineGroups,
  resumeRoutine,
  updateRoutine,
  type Routine,
  type RoutineGroupBoard,
} from "../lib/tasks";
import { formatDayOfMonth } from "../lib/ordinal";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatRoutineSchedule(routine: Routine): string {
  if (routine.schedule_type === "monthly") {
    return `Monthly on the ${formatDayOfMonth(routine.day_of_month ?? 1)}`;
  }
  const days = routine.days_of_week.map((day) => WEEKDAY_LABELS[day]).join(", ");
  const interval =
    routine.interval_weeks === 1
      ? "Every week"
      : `Every ${routine.interval_weeks} weeks`;
  return `${interval} on ${days}`;
}

type DragState = {
  routineId: string;
  sourceGroupId: string;
} | null;

export function RoutinesPage() {
  const [board, setBoard] = useState<RoutineGroupBoard[] | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [title, setTitle] = useState("");
  const [scheduleType, setScheduleType] = useState<"weekly" | "monthly">("weekly");
  const [selectedDays, setSelectedDays] = useState<number[]>([4]);
  const [dayOfMonth, setDayOfMonth] = useState("1");
  const [intervalWeeks, setIntervalWeeks] = useState("1");
  const [startsOn, setStartsOn] = useState("");
  const [plannerToday, setPlannerToday] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newGroupName, setNewGroupName] = useState("");
  const [dragState, setDragState] = useState<DragState>(null);
  const [draggingGroupId, setDraggingGroupId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setBoard(await fetchRoutineGroupBoard());
  }, []);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchTodayView()
      .then((view) => {
        if (!cancelled) {
          setStartsOn(view.reference_date);
          setPlannerToday(view.reference_date);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchRoutineGroupBoard()
      .then((groups) => {
        if (!cancelled) {
          setBoard(groups);
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
    setStartsOn(plannerToday);
    setEditingId(null);
  };

  const toggleDay = (day: number) => {
    setSelectedDays((current) =>
      current.includes(day)
        ? current.filter((value) => value !== day)
        : [...current, day].sort(),
    );
  };

  const loadRoutineForEdit = (routine: Routine) => {
    setEditingId(routine.id);
    setTitle(routine.title);
    setScheduleType(routine.schedule_type as "weekly" | "monthly");
    setSelectedDays(routine.days_of_week);
    setDayOfMonth(String(routine.day_of_month ?? 1));
    setIntervalWeeks(String(routine.interval_weeks));
    setStartsOn(routine.starts_on ?? plannerToday);
  };

  const buildPayload = () => {
    const payload = {
      title,
      schedule_type: scheduleType,
      starts_on: startsOn || plannerToday,
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
    setError(null);
    try {
      if (routine.status === "active") {
        await pauseRoutine(routine.id);
      } else if (routine.status === "paused") {
        await resumeRoutine(routine.id);
      }
      await reload();
    } catch (pauseError) {
      setError(
        pauseError instanceof Error ? pauseError.message : "Could not update routine",
      );
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      return;
    }
    setError(null);
    try {
      await createRoutineGroup(newGroupName.trim());
      setNewGroupName("");
      await reload();
    } catch (groupError) {
      setError(groupError instanceof Error ? groupError.message : "Could not create group");
    }
  };

  const handleDeleteGroup = async (group: RoutineGroupBoard) => {
    if (group.is_system) {
      return;
    }
    if (!window.confirm(`Delete group "${group.name}"? Routines move to Misc.`)) {
      return;
    }
    setError(null);
    try {
      await deleteRoutineGroup(group.id);
      await reload();
    } catch (deleteError) {
      setError(
        deleteError instanceof Error ? deleteError.message : "Could not delete group",
      );
    }
  };

  const handleRoutineDrop = async (
    targetGroupId: string,
    targetIndex: number,
    routineId: string,
  ) => {
    setError(null);
    try {
      await moveRoutineToGroup(routineId, {
        group_id: targetGroupId,
        sort_order: targetIndex,
      });
      await reload();
    } catch (moveError) {
      setError(moveError instanceof Error ? moveError.message : "Could not move routine");
    } finally {
      setDragState(null);
    }
  };

  const handleGroupDrop = async (targetGroupId: string) => {
    if (!draggingGroupId || draggingGroupId === targetGroupId || !board) {
      setDraggingGroupId(null);
      return;
    }
    const ids = board.map((group) => group.id);
    const fromIndex = ids.indexOf(draggingGroupId);
    const toIndex = ids.indexOf(targetGroupId);
    if (fromIndex < 0 || toIndex < 0) {
      return;
    }
    ids.splice(fromIndex, 1);
    ids.splice(toIndex, 0, draggingGroupId);
    setError(null);
    try {
      await reorderRoutineGroups(ids);
      await reload();
    } catch (reorderError) {
      setError(
        reorderError instanceof Error ? reorderError.message : "Could not reorder groups",
      );
    } finally {
      setDraggingGroupId(null);
    }
  };

  const totalRoutines =
    board?.reduce((count, group) => count + group.routines.length, 0) ?? 0;

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
            <FormField
              label="Repeat every N weeks"
              hint="1 = every week, 2 = every other week"
            >
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
          <FormField
            label="Day of month"
            hint="Uses the last day when a month is shorter"
          >
            <Input
              type="number"
              min={1}
              max={31}
              value={dayOfMonth}
              onChange={(event) => setDayOfMonth(event.target.value)}
            />
          </FormField>
        )}

        <FormField
          label="Starts on"
          hint="Occurrences are only generated from this date forward"
        >
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

      <section className="pf-panel pf-routine-groups-panel">
        <div className="pf-routine-groups-panel__header">
          <h2>Groups</h2>
          <div className="pf-routine-groups-panel__create">
            <Input
              value={newGroupName}
              onChange={(event) => setNewGroupName(event.target.value)}
              placeholder="New group name"
            />
            <Button variant="secondary" onClick={() => void handleCreateGroup()}>
              Add group
            </Button>
          </div>
        </div>
        <p className="pf-muted">
          Drag routines between groups to organize them. Control week/month visibility in
          Settings.
        </p>
      </section>

      {board === null ? <LoadingIndicator label="Loading routines" /> : null}
      {board && totalRoutines === 0 ? (
        <EmptyState
          title="No routines yet"
          description="Create a weekly or monthly routine to generate occurrences in Week and Today."
        />
      ) : null}
      {board && totalRoutines > 0 ? (
        <div className="pf-routine-groups">
          {board.map((group) => {
            const isCollapsed = collapsed[group.id] ?? false;
            return (
              <section
                key={group.id}
                className="pf-routine-group"
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  if (dragState) {
                    void handleRoutineDrop(
                      group.id,
                      group.routines.length,
                      dragState.routineId,
                    );
                    return;
                  }
                  void handleGroupDrop(group.id);
                }}
              >
                <header
                  className="pf-routine-group__header"
                  draggable
                  onDragStart={() => setDraggingGroupId(group.id)}
                  onDragEnd={() => setDraggingGroupId(null)}
                >
                  <button
                    type="button"
                    className="pf-routine-group__toggle"
                    aria-expanded={!isCollapsed}
                    onClick={() =>
                      setCollapsed((current) => ({
                        ...current,
                        [group.id]: !isCollapsed,
                      }))
                    }
                  >
                    {isCollapsed ? "▸" : "▾"} {group.name}
                    <span className="pf-muted">({group.routines.length})</span>
                  </button>
                  {!group.is_system ? (
                    <Button variant="ghost" onClick={() => void handleDeleteGroup(group)}>
                      Delete
                    </Button>
                  ) : null}
                </header>
                {!isCollapsed ? (
                  <ul className="pf-task-list pf-routine-group__items">
                    {group.routines.map((routine, index) => (
                      <li
                        key={routine.id}
                        className={`pf-task-row pf-routine-row${
                          dragState?.routineId === routine.id
                            ? " pf-routine-row--dragging"
                            : ""
                        }`}
                        draggable
                        onDragStart={() =>
                          setDragState({
                            routineId: routine.id,
                            sourceGroupId: group.id,
                          })
                        }
                        onDragEnd={() => setDragState(null)}
                        onDragOver={(event) => event.preventDefault()}
                        onDrop={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          if (!dragState) {
                            return;
                          }
                          void handleRoutineDrop(group.id, index, dragState.routineId);
                        }}
                      >
                        <div className="pf-task-row__main">
                          <p className="pf-task-row__title">{routine.title}</p>
                          <p className="pf-muted">
                            {formatRoutineSchedule(routine)}
                            {routine.starts_on ? ` · starts ${routine.starts_on}` : ""} ·{" "}
                            {routine.status}
                          </p>
                        </div>
                        <div className="pf-task-row__actions">
                          <Button
                            variant="secondary"
                            onClick={() => loadRoutineForEdit(routine)}
                          >
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
              </section>
            );
          })}
        </div>
      ) : null}
    </AppShell>
  );
}
