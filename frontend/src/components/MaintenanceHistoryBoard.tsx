import type { MaintenanceHistoryRow } from "../lib/tasks";

export interface MaintenanceHistoryBoardProps {
  rows: MaintenanceHistoryRow[];
  historyLimit: number;
  onHistoryLimitChange: (limit: number) => void;
  onOpenItem?: (item: MaintenanceHistoryRow["maintenance"]) => void;
}

function formatCompletionDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function MaintenanceHistoryBoard({
  rows,
  historyLimit,
  onHistoryLimitChange,
  onOpenItem,
}: MaintenanceHistoryBoardProps) {
  const maxColumns = Math.max(0, ...rows.map((row) => row.completions.length));

  return (
    <section className="pf-maintenance-history" aria-label="Maintenance history">
      <div className="pf-maintenance-history__controls">
        <label>
          History columns
          <select
            value={historyLimit}
            onChange={(event) => onHistoryLimitChange(Number(event.target.value))}
            aria-label="History column limit"
          >
            <option value={10}>Latest 10</option>
            <option value={25}>Latest 25</option>
            <option value={500}>All</option>
          </select>
        </label>
      </div>

      <div
        className="pf-maintenance-history__desktop"
        role="table"
        aria-label="Maintenance history table"
      >
        <div className="pf-maintenance-history__header" role="row">
          <div className="pf-maintenance-history__pinned" role="columnheader">
            Maintenance
          </div>
          <div className="pf-maintenance-history__pinned" role="columnheader">
            Current / next
          </div>
          <div className="pf-maintenance-history__scroll" role="rowgroup">
            <div className="pf-maintenance-history__scroll-inner">
              {Array.from({ length: maxColumns }, (_, index) => (
                <div
                  key={`col-${index}`}
                  className="pf-maintenance-history__cell"
                  role="columnheader"
                >
                  {index === 0 ? "Latest" : index === 1 ? "Previous" : "Older →"}
                </div>
              ))}
            </div>
          </div>
        </div>

        {rows.map((row) => (
          <div
            key={row.maintenance.id}
            className="pf-maintenance-history__row"
            role="row"
            onClick={() => onOpenItem?.(row.maintenance)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onOpenItem?.(row.maintenance);
              }
            }}
            tabIndex={onOpenItem ? 0 : undefined}
          >
            <div className="pf-maintenance-history__pinned" role="cell">
              <strong>{row.maintenance.title}</strong>
              {row.maintenance.category ? (
                <p className="pf-muted">{row.maintenance.category}</p>
              ) : null}
            </div>
            <div className="pf-maintenance-history__pinned" role="cell">
              {row.current_next_label}
            </div>
            <div className="pf-maintenance-history__scroll" role="cell">
              <div className="pf-maintenance-history__scroll-inner">
                {row.completions.length === 0 ? (
                  <div className="pf-maintenance-history__cell pf-muted">
                    Add first record
                  </div>
                ) : (
                  row.completions.map((completion) => (
                    <div key={completion.id} className="pf-maintenance-history__cell">
                      {formatCompletionDate(completion.completed_on)}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="pf-maintenance-history__mobile">
        {rows.map((row) => (
          <details
            key={row.maintenance.id}
            className="pf-maintenance-history__mobile-row"
          >
            <summary>
              <strong>{row.maintenance.title}</strong>
              <span className="pf-muted"> · {row.current_next_label}</span>
            </summary>
            {row.completions.length === 0 ? (
              <p className="pf-muted">Add first record</p>
            ) : (
              <ul>
                {row.completions.map((completion) => (
                  <li key={completion.id}>
                    {formatCompletionDate(completion.completed_on)}
                    {completion.notes ? ` — ${completion.notes}` : ""}
                  </li>
                ))}
              </ul>
            )}
          </details>
        ))}
      </div>
    </section>
  );
}
