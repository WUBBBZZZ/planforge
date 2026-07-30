import { EmptyState } from "../EmptyState";
import { PeriodNav } from "../PeriodNav";
import { PlannerItemRow } from "../PlannerItemRow";
import { todayIsoLocal, weekdayLabels } from "../../lib/dates";
import { type MonthView, type PlannerItem } from "../../lib/tasks";

export interface MonthViewContentProps {
  view: MonthView;
  periodLabel: string;
  calendar: Array<
    { kind: "pad" } | { kind: "day"; date: string; items: PlannerItem[] }
  >;
  extraBuckets: MonthView["days"];
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  onReload: () => Promise<void>;
}

const MONTH_DAY_ITEM_LIMIT = 6;

function monthDayItems(items: PlannerItem[]): PlannerItem[] {
  return items.filter(
    (item) => item.span_segment !== "middle" && item.span_segment !== "end",
  );
}

function MonthDayCell({
  date,
  items,
}: {
  date: string;
  items: PlannerItem[];
}) {
  const displayItems = monthDayItems(items);
  const visibleItems = displayItems.slice(0, MONTH_DAY_ITEM_LIMIT);
  const hiddenCount = displayItems.length - visibleItems.length;
  const isToday = date === todayIsoLocal();
  const dayNumber = Number(date.split("-")[2]);

  return (
    <td className="pf-month-day-cell">
      <article className={`pf-month-day${isToday ? " pf-month-day--today" : ""}`}>
        <header className="pf-month-day__header">
          <a
            className={`pf-month-day__date${isToday ? " pf-month-day__date--today" : ""}`}
            href={`/today?date=${date}`}
            aria-label={`Open ${date}`}
          >
            {dayNumber}
          </a>
        </header>
        {visibleItems.length > 0 ? (
          <ul className="pf-month-day__items">
            {visibleItems.map((item) => (
              <PlannerItemRow
                key={`${item.kind}-${item.item_id}-${item.span_segment ?? "single"}`}
                item={item}
                readOnly
                previewSize="month"
                onChanged={async () => {}}
              />
            ))}
            {hiddenCount > 0 ? (
              <li className="pf-month-day__more">
                <a href={`/today?date=${date}`}>+{hiddenCount} more</a>
              </li>
            ) : null}
          </ul>
        ) : null}
      </article>
    </td>
  );
}

function chunkCalendar<T>(cells: T[], size: number): T[][] {
  const weeks: T[][] = [];
  for (let index = 0; index < cells.length; index += size) {
    weeks.push(cells.slice(index, index + size));
  }
  return weeks;
}

export function MonthViewContent({
  view,
  periodLabel,
  calendar,
  extraBuckets,
  onPrevious,
  onNext,
  onToday,
  onReload,
}: MonthViewContentProps) {
  const isEmpty =
    calendar.every((cell) => cell.kind === "pad" || cell.items.length === 0) &&
    extraBuckets.every((group) => group.items.length === 0);
  const weeks = chunkCalendar(calendar, 7);

  return (
    <div className="pf-month-view">
      <PeriodNav
        label={periodLabel}
        previousLabel="Previous month"
        nextLabel="Next month"
        todayLabel="This month"
        onPrevious={onPrevious}
        onNext={onNext}
        onToday={onToday}
      />

      <div className="pf-month-grid-wrap">
        <table className="pf-month-grid" aria-label={periodLabel}>
          <thead>
            <tr>
              {weekdayLabels(view.week_start_day).map((label) => (
                <th key={label} scope="col" className="pf-month-grid__weekday">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {weeks.map((week, weekIndex) => (
              <tr key={`week-${weekIndex}`}>
                {week.map((cell, cellIndex) =>
                  cell.kind === "pad" ? (
                    <td
                      key={`pad-${weekIndex}-${cellIndex}`}
                      className="pf-month-grid__pad"
                      aria-hidden="true"
                    />
                  ) : (
                    <MonthDayCell key={cell.date} date={cell.date} items={cell.items} />
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isEmpty ? (
        <EmptyState
          title="No items this month"
          description="Capture a task, appointment, or routine to populate this view."
        />
      ) : null}

      {extraBuckets.length > 0 ? (
        <div className="pf-week-buckets">
          {extraBuckets.map((group) => {
            const sectionTitle =
              group.label === "upcoming"
                ? "Upcoming"
                : group.label === "backlog"
                  ? "Backlog"
                  : "Unscheduled";
            return (
              <section
                key={group.label ?? "bucket"}
                className="pf-week-bucket"
                aria-labelledby={`month-${group.label ?? "bucket"}`}
              >
                <h2 id={`month-${group.label ?? "bucket"}`}>{sectionTitle}</h2>
                <ul className="pf-task-list pf-week-bucket__items">
                  {group.items.map((item) => (
                    <PlannerItemRow
                      key={`${item.kind}-${item.item_id}`}
                      item={item}
                      readOnly
                      onChanged={onReload}
                    />
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
