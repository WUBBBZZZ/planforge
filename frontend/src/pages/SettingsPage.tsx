import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { Input } from "../components/Input";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { Select } from "../components/Select";
import {
  createWeeklyTarget,
  fetchSettings,
  listRoutineGroups,
  updateRoutineGroup,
  updateSetting,
  type RoutineGroup,
} from "../lib/tasks";
import { applyTheme, getStoredThemePreference } from "../lib/theme";

const POLICY_FIELDS = [
  {
    key: "today.include_rolled_tasks",
    label: "Show overdue tasks in Today",
    options: [
      { value: "yes", label: "Yes" },
      { value: "no", label: "No" },
    ],
  },
  {
    key: "week.include_overdue_tasks",
    label: "Show overdue tasks in Week",
    options: [
      { value: "yes", label: "Yes" },
      { value: "no", label: "No" },
    ],
  },
  {
    key: "week.start_day",
    label: "Week starts on",
    options: [
      { value: "monday", label: "Monday" },
      { value: "sunday", label: "Sunday" },
      { value: "saturday", label: "Saturday" },
    ],
  },
  {
    key: "routine.horizon_days",
    label: "Routine horizon",
    options: [
      { value: "short", label: "14 days" },
      { value: "medium", label: "30 days" },
      { value: "long", label: "90 days" },
    ],
  },
  {
    key: "maintenance.lead_days",
    label: "Maintenance lead days",
    options: [
      { value: "7", label: "7 days" },
      { value: "14", label: "14 days" },
      { value: "30", label: "30 days" },
    ],
  },
];

export function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, string> | null>(null);
  const [routineGroups, setRoutineGroups] = useState<RoutineGroup[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchSettings()
      .then((values) => {
        if (!cancelled) {
          setSettings(values);
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error ? loadError.message : "Could not load settings",
          );
        }
      });
    listRoutineGroups()
      .then((groups) => {
        if (!cancelled) {
          setRoutineGroups(groups);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRoutineGroups([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const runAction = async (action: () => Promise<void>, successMessage: string) => {
    setError(null);
    try {
      await action();
      setMessage(successMessage);
    } catch (actionError) {
      setMessage(null);
      setError(actionError instanceof Error ? actionError.message : "Action failed");
    }
  };

  const handlePolicyChange = async (key: string, value: string) => {
    await runAction(async () => {
      const updated = await updateSetting(key, value);
      setSettings(updated);
    }, "Settings updated.");
  };

  const handleGroupVisibility = async (groupId: string, weekVisible: boolean) => {
    await runAction(async () => {
      const updated = await updateRoutineGroup(groupId, { week_visible: weekVisible });
      setRoutineGroups((current) =>
        current
          ? current.map((group) => (group.id === updated.id ? updated : group))
          : current,
      );
    }, "Routine group visibility updated.");
  };

  const seedWeeklyTarget = async () => {
    await runAction(async () => {
      await createWeeklyTarget({
        title: "Exercise 3 times",
        target_count: 3,
      });
    }, "Demo weekly target created.");
  };

  return (
    <AppShell currentPath="/settings" title="Settings">
      {settings === null && error === null ? (
        <LoadingIndicator label="Loading settings" />
      ) : null}
      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}
      {settings ? (
        <div className="pf-settings">
          <FormField label="Planner timezone (IANA)">
            <Input
              value={settings.timezone ?? "UTC"}
              onChange={(event) => {
                setSettings({ ...settings, timezone: event.target.value });
              }}
              onBlur={(event) =>
                void handlePolicyChange("timezone", event.target.value)
              }
            />
          </FormField>
          {POLICY_FIELDS.map((field) => (
            <FormField key={field.key} label={field.label}>
              <Select
                value={settings[field.key]}
                options={field.options}
                onChange={(event) =>
                  void handlePolicyChange(field.key, event.target.value)
                }
              />
            </FormField>
          ))}
          {routineGroups && routineGroups.length > 0 ? (
            <section className="pf-settings__routine-groups" aria-labelledby="routine-group-visibility">
              <h2 id="routine-group-visibility">Routine groups on Week &amp; Month</h2>
              <p className="pf-muted">
                Hidden groups stay off the week and month calendars. Today always shows all
                routines due that day.
              </p>
              <ul className="pf-settings__routine-group-list">
                {routineGroups.map((group) => (
                  <li key={group.id} className="pf-settings__routine-group-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={group.week_visible}
                        onChange={(event) =>
                          void handleGroupVisibility(group.id, event.target.checked)
                        }
                      />
                      {group.name}
                    </label>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          <div className="pf-settings__actions">
            <Button variant="secondary" onClick={() => void seedWeeklyTarget()}>
              Add demo weekly target
            </Button>
          </div>
        </div>
      ) : null}
      {message ? <p className="pf-muted">{message}</p> : null}
    </AppShell>
  );
}
