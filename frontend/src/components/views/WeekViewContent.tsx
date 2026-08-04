import { useEffect, useState } from "react";

import { Button } from "../Button";
import { PeriodNav } from "../PeriodNav";
import { PlannerItemRow } from "../PlannerItemRow";
import { WeeklyTargetDialog, type WeeklyTargetDraft } from "../WeeklyTargetDialog";
import { todayIsoLocal } from "../../lib/dates";
import { formatDisplayDate, type WeekView } from "../../lib/tasks";
import { useNarrowViewport } from "../../lib/viewport";

export interface WeekViewContentProps {
  view: WeekView;
  periodLabel: string;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  onReload: () => Promise<void>;
  onLogTarget: (targetId: string) => Promise<void>;
  onSaveTarget: (draft: WeeklyTargetDraft) => Promise<void>;
  onDeleteTarget: (targetId: string) => Promise<void>;
}

function bucketSectionTitle(label: string | null | undefined): string {
  switch (label) {
    case "upcoming":
      return "Upcoming";
    case "backlog":
      return "Backlog";
    default:
      return "Unscheduled";
  }
}

export function WeekViewContent({
  view,
  periodLabel,
  onPrevious,
  onNext,
  onToday,
  onReload,
  onLogTarget,
  onSaveTarget,
  onDeleteTarget,
}: WeekViewContentProps) {
  const [targetDialogOpen, setTargetDialogOpen] = useState(false);
  const [targetDraft, setTargetDraft] = useState<WeeklyTargetDraft | null>(null);
  const isNarrow = useNarrowViewport();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const calendarDays = view.days.filter((group) => group.date !== null);
  const bucketGroups = view.days.filter(
    (group) => group.date === null && group.items.length > 0,
  );

  useEffect(() => {
    const today = todayIsoLocal();
    const todayInWeek = calendarDays.find((group) => group.date === today);
    setSelectedDate(todayInWeek?.date ?? calendarDays[0]?.date ?? null);
  }, [view.week_start, view.week_end]);

  const openCreateTarget = () => {
    setTargetDraft({ title: "", targetCount: 1 });
    setTargetDialogOpen(true);
  };

  const openEditTarget = (target: WeekView["targets"][number]) => {
    setTargetDraft({
      targetId: target.target_id,
      title: target.title,
      targetCount: target.target_count,
    });
    setTargetDialogOpen(true);
  };

  const renderDayColumn = (group: WeekView["days"][number], interactive: boolean) => {
    const sectionKey = group.date ?? "day";
    const dayNumber = group.date?.split("-")[2];
    const weekday = group.date ? formatDisplayDate(group.date).split(",")[0] : "";

    return (
      <section
        key={sectionKey}
        className="pf-week-column"
        aria-labelledby={`week-day-${sectionKey}`}
      >
        <header className="pf-week-column__header">
          <h2 id={`week-day-${sectionKey}`}>
            <span className="pf-week-column__weekday">{weekday}</span>
            <span className="pf-week-column__date">{dayNumber}</span>
          </h2>
        </header>
        {group.items.length === 0 ? (
          <p className="pf-muted pf-week-column__empty">No items</p>
        ) : (
          <ul className="pf-task-list pf-week-column__items">
            {group.items.map((item) => (
              <PlannerItemRow
                key={`${item.kind}-${item.item_id}`}
                item={item}
                readOnly={!interactive}
                completedOnDate={group.date ?? undefined}
                onChanged={onReload}
              />
            ))}
          </ul>
        )}
      </section>
    );
  };

  const selectedDay = calendarDays.find((group) => group.date === selectedDate) ?? null;
  const selectedDayIndex = calendarDays.findIndex((group) => group.date === selectedDate);

  const selectRelativeDay = (offset: number) => {
    const nextIndex = selectedDayIndex + offset;
    if (nextIndex < 0 || nextIndex >= calendarDays.length) {
      return;
    }
    const nextDate = calendarDays[nextIndex]?.date;
    if (nextDate) {
      setSelectedDate(nextDate);
    }
  };

  return (
    <div className="pf-week-view">
      <PeriodNav
        label={periodLabel}
        previousLabel="Previous week"
        nextLabel="Next week"
        todayLabel="This week"
        onPrevious={onPrevious}
        onNext={onNext}
        onToday={onToday}
      />

      <section className="pf-week-targets" aria-labelledby="week-targets">
        <div className="pf-week-targets__header">
          <h2 id="week-targets">Weekly targets</h2>
          <Button variant="secondary" onClick={openCreateTarget}>
            Add target
          </Button>
        </div>
        {view.targets.length > 0 ? (
          <ul className="pf-target-list">
            {view.targets.map((target) => (
              <li key={target.target_id} className="pf-target-row">
                <div className="pf-target-row__main">
                  <span className="pf-target-row__label">{target.title}</span>
                  <span className="pf-target-row__progress">
                    {target.completed_count}/{target.target_count} this week
                  </span>
                </div>
                <div className="pf-target-row__actions">
                  <Button
                    variant="secondary"
                    onClick={() => void onLogTarget(target.target_id)}
                    aria-label={`Log progress for ${target.title}`}
                  >
                    +1
                  </Button>
                  <Button variant="ghost" onClick={() => openEditTarget(target)}>
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      if (
                        window.confirm(
                          `Delete "${target.title}"? This cannot be undone.`,
                        )
                      ) {
                        void onDeleteTarget(target.target_id);
                      }
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="pf-muted">
            Track habits or goals you want to hit a set number of times each week.
          </p>
        )}
      </section>

      {isNarrow ? (
        <>
          <div className="pf-week-day-nav">
            <Button
              variant="secondary"
              disabled={selectedDayIndex <= 0}
              onClick={() => selectRelativeDay(-1)}
            >
              Previous day
            </Button>
            <Button
              variant="secondary"
              disabled={selectedDayIndex < 0 || selectedDayIndex >= calendarDays.length - 1}
              onClick={() => selectRelativeDay(1)}
            >
              Next day
            </Button>
          </div>
          <div className="pf-week-day-strip" role="tablist" aria-label="Week days">
            {calendarDays.map((group) => {
              if (!group.date) {
                return null;
              }
              const dayNumber = group.date.split("-")[2];
              const weekday = formatDisplayDate(group.date).split(",")[0];
              const isActive = group.date === selectedDate;
              return (
                <button
                  key={group.date}
                  type="button"
                  role="tab"
                  className={`pf-week-day-strip__day${isActive ? " is-active" : ""}`}
                  aria-selected={isActive}
                  onClick={() => setSelectedDate(group.date)}
                >
                  <span className="pf-week-day-strip__weekday">{weekday}</span>
                  <span className="pf-week-day-strip__date">{dayNumber}</span>
                </button>
              );
            })}
          </div>
          {selectedDay ? (
            <div className="pf-week-board pf-week-board--single">
              {renderDayColumn(selectedDay, true)}
            </div>
          ) : null}
        </>
      ) : (
        <div className="pf-week-board">
          {calendarDays.map((group) => renderDayColumn(group, false))}
        </div>
      )}

      {bucketGroups.length > 0 ? (
        <div className="pf-week-buckets">
          {bucketGroups.map((group) => {
            const sectionTitle = bucketSectionTitle(group.label);
            return (
              <section
                key={group.label ?? "bucket"}
                className="pf-week-bucket"
                aria-labelledby={`week-${group.label ?? "bucket"}`}
              >
                <h2 id={`week-${group.label ?? "bucket"}`}>{sectionTitle}</h2>
                <ul className="pf-task-list pf-week-bucket__items">
                  {group.items.map((item) => (
                    <PlannerItemRow
                      key={`${item.kind}-${item.item_id}`}
                      item={item}
                      readOnly={!isNarrow}
                      onChanged={onReload}
                    />
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      ) : null}

      <WeeklyTargetDialog
        open={targetDialogOpen}
        draft={targetDraft}
        onClose={() => setTargetDialogOpen(false)}
        onSave={onSaveTarget}
      />
    </div>
  );
}
