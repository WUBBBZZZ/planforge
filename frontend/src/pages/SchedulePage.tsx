import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { AppointmentEditDialog } from "../components/AppointmentEditDialog";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import {
  appointmentStatusLabel,
  archiveAppointment,
  cancelAppointment,
  completeAppointment,
  deleteAppointment,
  formatAppointmentSchedule,
  listAppointments,
  reopenAppointment,
  restoreAppointment,
  type Appointment,
  type AppointmentListFilter,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

type ScheduleState =
  | { kind: "loading" }
  | { kind: "ready"; items: Appointment[] }
  | { kind: "error"; message: string };

const FILTERS: Array<{ id: AppointmentListFilter; label: string }> = [
  { id: "upcoming", label: "Upcoming" },
  { id: "today", label: "Today" },
  { id: "past", label: "Past" },
  { id: "cancelled", label: "Cancelled" },
  { id: "archived", label: "Archived" },
];

export function SchedulePage() {
  const [filter, setFilter] = useState<AppointmentListFilter>("upcoming");
  const [search, setSearch] = useState("");
  const [state, setState] = useState<ScheduleState>({ kind: "loading" });
  const [actionError, setActionError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Appointment | null>(null);

  const reload = async () => {
    try {
      const items = await listAppointments({
        filter,
        search: search.trim() || undefined,
      });
      setState({ kind: "ready", items });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load appointments";
      setState({ kind: "error", message });
    }
  };

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    listAppointments({
      filter,
      search: search.trim() || undefined,
    })
      .then((items) => {
        if (!cancelled) {
          setState({ kind: "ready", items });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Could not load appointments";
          setState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filter, search]);

  const runAction = async (action: () => Promise<void>) => {
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed");
    }
  };

  const openCreate = () => {
    setEditing(null);
    setDialogOpen(true);
  };

  const openEdit = (appointment: Appointment) => {
    setEditing(appointment);
    setDialogOpen(true);
  };

  return (
    <AppShell
      currentPath="/schedule"
      title="Schedule"
      actions={<Button onClick={openCreate}>New appointment</Button>}
    >
      <div className="pf-schedule-toolbar">
        <div
          className="pf-schedule-filters"
          role="group"
          aria-label="Appointment filters"
        >
          {FILTERS.map((entry) => (
            <Button
              key={entry.id}
              variant={filter === entry.id ? "secondary" : "ghost"}
              onClick={() => setFilter(entry.id)}
              aria-pressed={filter === entry.id}
            >
              {entry.label}
            </Button>
          ))}
        </div>
        <Input
          type="search"
          placeholder="Search title, notes, location, category"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          aria-label="Search appointments"
        />
      </div>

      {actionError ? (
        <p className="pf-form-field__error" role="alert">
          {actionError}
        </p>
      ) : null}

      {state.kind === "loading" ? (
        <LoadingIndicator label="Loading appointments" />
      ) : null}
      {state.kind === "error" ? (
        <p className="pf-form-field__error" role="alert">
          {state.message}
        </p>
      ) : null}

      {state.kind === "ready" && state.items.length === 0 ? (
        <EmptyState
          title="No appointments here"
          description="Create an appointment or try another filter."
        />
      ) : null}

      {state.kind === "ready" && state.items.length > 0 ? (
        <ul className="pf-task-list">
          {state.items.map((appointment) => (
            <li key={appointment.id} className="pf-task-row">
              <div className="pf-task-row__main">
                <p className="pf-task-row__title">{appointment.title}</p>
                <div className="pf-task-row__meta">
                  <Badge tone="neutral">
                    {appointmentStatusLabel(appointment.status)}
                  </Badge>
                  {appointment.category ? <Badge>{appointment.category}</Badge> : null}
                  <Badge>{formatAppointmentSchedule(appointment)}</Badge>
                  {appointment.location ? <Badge>{appointment.location}</Badge> : null}
                </div>
                {appointment.notes ? (
                  <p className="pf-muted">{appointment.notes}</p>
                ) : null}
              </div>
              <div className="pf-task-row__actions">
                {appointment.status === "scheduled" ? (
                  <>
                    <Button
                      variant="secondary"
                      onClick={() =>
                        void runAction(async () => {
                          await completeAppointment(appointment.id);
                        })
                      }
                    >
                      Complete
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        void runAction(async () => {
                          await cancelAppointment(appointment.id);
                        })
                      }
                    >
                      Cancel
                    </Button>
                    <Button variant="ghost" onClick={() => openEdit(appointment)}>
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        void runAction(async () => {
                          await archiveAppointment(appointment.id);
                        })
                      }
                    >
                      Archive
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        void runAction(async () => {
                          await deleteAppointment(appointment.id);
                        })
                      }
                    >
                      Delete
                    </Button>
                  </>
                ) : null}
                {appointment.status === "cancelled" ? (
                  <Button
                    variant="secondary"
                    onClick={() =>
                      void runAction(async () => {
                        await reopenAppointment(appointment.id);
                      })
                    }
                  >
                    Reopen
                  </Button>
                ) : null}
                {appointment.status === "archived" ? (
                  <Button
                    variant="secondary"
                    onClick={() =>
                      void runAction(async () => {
                        await restoreAppointment(appointment.id);
                      })
                    }
                  >
                    Restore
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <AppointmentEditDialog
        open={dialogOpen}
        appointment={editing}
        onClose={() => setDialogOpen(false)}
        onSaved={() => void reload()}
      />
    </AppShell>
  );
}
