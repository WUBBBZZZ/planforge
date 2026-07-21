# Acceptance criteria

Testable statements per workflow. Use for manual test plans and automated tests
once features exist. Wording uses fabricated examples only.

## Capture

- **AC-CAP-1:** Given an empty backlog, when the user saves "Demo backlog item"
  to the backlog, then the item appears in the backlog list with state `active`.
- **AC-CAP-2:** When the user saves a task with due date today, then it appears
  in Today without appearing in backlog.
- **AC-CAP-3:** Invalid empty title is rejected with a visible validation message;
  no entity is created.

## Plan the week

- **AC-PLW-1:** When the user promotes backlog item "Example errand" to a task
  due Friday, then backlog state is `promoted` and the task appears on Friday
  in Week view.
- **AC-PLW-2:** Week view respects `week.start_day` preference (see policies).
- **AC-PLW-3:** Weekly target "Exercise 3 times" shows progress 0/3 until
  completions are recorded.

## Execute Today

- **AC-TOD-1:** Today lists tasks due today, today's routine occurrences, and
  today's appointments when policies include them.
- **AC-TOD-2:** Completing "Water the plants" writes a completion record and
  removes the item from pending Today list (or shows completed per policy).
- **AC-TOD-3:** With backend stopped, Today shows a clear error without exposing
  stack traces or internal paths.

## Routines and occurrences

- **AC-ROU-1:** Active routine "Weekday demo stretch" generates pending
  occurrences for each weekday within `routine.horizon_days`.
- **AC-ROU-2:** Completing an occurrence does not delete the routine definition.
- **AC-ROU-3:** Paused routine generates no new occurrences until resumed.

## Maintenance

- **AC-MNT-1:** Maintenance "Replace demo filter" with 90-day interval shows
  next due date after completion.
- **AC-MNT-2:** Maintenance appears in Today within `maintenance.lead_days` of
  due date.

## Appointments

- **AC-APT-1:** Manual appointment stores start/end in consistent timezone
  fields per ADR 0006.
- **AC-APT-2:** Appointment on today appears in Today and Week views.

## Settings and policies

- **AC-SET-1:** Changing `today.include_rolled_tasks` updates Today contents on
  next load without server restart.
- **AC-SET-2:** All policy values are validated server-side; unknown option keys
  return 422.

## Non-functional (all features)

- **AC-NF-1:** API binds to 127.0.0.1 in development configuration.
- **AC-NF-2:** No planner content appears in application logs.
- **AC-NF-3:** Keyboard users can complete primary actions on each screen
  (Tab, Enter, visible focus).

## Definition of done

A feature implementing these criteria also passes lint, tests, pre-commit, and CI
per the roadmap definition of done.
