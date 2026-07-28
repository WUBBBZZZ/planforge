import { EmptyState } from "../EmptyState";
import { PlannerItemRow } from "../PlannerItemRow";
import { formatDisplayDate, type TodayView } from "../../lib/tasks";

export interface TodayViewContentProps {
  view: TodayView;
  onReload: () => Promise<void>;
}

export function TodayViewContent({ view, onReload }: TodayViewContentProps) {
  const overdueItems = view.items.filter((item) => item.is_overdue && !item.is_completed);
  const dueTodayItems = view.items.filter(
    (item) => !item.is_overdue && !item.is_completed,
  );
  const completedItems = view.items.filter((item) => item.is_completed);

  if (view.items.length === 0) {
    return (
      <EmptyState
        title="Nothing due today"
        description="Tasks, routines, appointments, and maintenance within the lead window appear here."
      />
    );
  }

  return (
    <div className="pf-today-view">
      <p className="pf-muted">{formatDisplayDate(view.reference_date)}</p>

      {overdueItems.length > 0 ? (
        <section className="pf-today-section" aria-labelledby="today-overdue">
          <h2 id="today-overdue">Overdue</h2>
          <ul className="pf-task-list">
            {overdueItems.map((item) => (
              <PlannerItemRow
                key={`${item.kind}-${item.item_id}`}
                item={item}
                onChanged={onReload}
              />
            ))}
          </ul>
        </section>
      ) : null}

      {dueTodayItems.length > 0 ? (
        <section className="pf-today-section" aria-labelledby="today-due">
          <h2 id="today-due">Due today</h2>
          <ul className="pf-task-list">
            {dueTodayItems.map((item) => (
              <PlannerItemRow
                key={`${item.kind}-${item.item_id}`}
                item={item}
                onChanged={onReload}
              />
            ))}
          </ul>
        </section>
      ) : null}

      {completedItems.length > 0 ? (
        <section className="pf-today-section" aria-labelledby="today-completed">
          <h2 id="today-completed">Completed today</h2>
          <ul className="pf-task-list">
            {completedItems.map((item) => (
              <PlannerItemRow
                key={`${item.kind}-${item.item_id}`}
                item={item}
                onChanged={onReload}
              />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
