"""Planner view endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.core.policy_defaults import get_policy_snapshot
from planforge.domain.clock import SystemClock
from planforge.domain.local_date import LocalDate
from planforge.schemas.views import TodayViewResponse, WeekViewResponse
from planforge.services.today_view import assemble_today_view
from planforge.services.week_view import assemble_week_view, week_bounds

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/today", response_model=TodayViewResponse)
def today_view_endpoint(
    session: Session = Depends(get_db),
    reference: date | None = Query(default=None, alias="date"),
) -> TodayViewResponse:
    """Return the Today view for a reference date."""
    clock = SystemClock()
    reference_date = (
        LocalDate.from_date(reference) if reference is not None else clock.today()
    )
    policies = get_policy_snapshot()
    view = assemble_today_view(
        session=session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=reference_date,
        policies=policies,
    )
    return TodayViewResponse.from_view(view)


@router.get("/week", response_model=WeekViewResponse)
def week_view_endpoint(
    session: Session = Depends(get_db),
    week_start_param: date | None = Query(default=None, alias="week_start"),
) -> WeekViewResponse:
    """Return the Week view for a week starting on the given date."""
    policies = get_policy_snapshot()
    if week_start_param is not None:
        week_start = LocalDate.from_date(week_start_param)
    else:
        clock = SystemClock()
        week_start, _ = week_bounds(
            reference_date=clock.today(),
            week_start_day=policies.week_start_day,
        )

    view = assemble_week_view(
        session=session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        policies=policies,
    )
    return WeekViewResponse.from_view(view)
