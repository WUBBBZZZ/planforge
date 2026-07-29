"""Time source for planner views."""

from planforge.domain.planner_clock import PlannerClock

# Backward-compatible alias for tests and callers migrating from env-based clock.
SystemClock = PlannerClock

__all__ = ["PlannerClock", "SystemClock"]
