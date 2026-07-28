import { EmptyState } from "../EmptyState";
import { PeriodNav } from "../PeriodNav";
import { PlannerItemRow } from "../PlannerItemRow";
import { weekdayLabels } from "../../lib/dates";
import { itemKindLabel, type MonthView, type PlannerItem } from "../../lib/tasks";

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

function MonthDayCell({
  date,
  items,
  onChanged,
}: {
  date: string;
  items: PlannerItem[];
  onChanged: () => Promise<void>;
}) {
  const visibleItems = items.slice(0, 3);
  const hiddenCount = items.length - visibleItems.length;

  return (
    <td className="pf-month-day-cell">
      <article className="pf-month-day">
        <header className="pf-month-day__header">
          <a className="pf-month-day__date" href={`/week?week_start=${date}`}>
            {Number(date.split("-")[2])}
          </a>
        </header>
        {items.length === 0 ? (
          <p className="pf-muted pf-month-day__empty">—</p>
        ) : (
          <ul className="pf-month-day__items">
            {visibleItems.map((item) => (
              <li key={`${item.kind}-${item.item_id}`} className="pf-month-day__item">
                <span className="pf-month-day__item-kind">
                  {itemKindLabel(item.kind)}
                </span>
                <span>{item.title}</span>
              </li>
            ))}
            {hiddenCount > 0 ? (
              <li className="pf-month-day__more">+{hiddenCount} more</li>
            ) : null}
          </ul>
        )}
        {items.length > 0 ? (
          <details className="pf-month-day__details">
            <summary>Manage items</summary>
            <ul className="pf-task-list">
              {items.map((item) => (
                <PlannerItemRow
                  key={`${item.kind}-${item.item_id}`}
                  item={item}
                  onChanged={onChanged}
                />
              ))}
            </ul>
          </details>
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
                  <MonthDayCell
                    key={cell.date}
                    date={cell.date}
                    items={cell.items}
                    onChanged={onReload}
                  />
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>

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
              group.label === "upcoming" ? "Upcoming" : "Unscheduled";
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
