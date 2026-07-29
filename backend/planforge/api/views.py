"""Planner view endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import InvalidLocalDateError, LocalDate
from planforge.domain.planner_clock import PlannerClock
from planforge.schemas.views import (
    MonthViewResponse,
    TodayViewResponse,
    WeekViewResponse,
)
from planforge.services.month_view import assemble_month_view
from planforge.services.settings_service import get_policy_snapshot
from planforge.services.today_view import assemble_today_view
from planforge.services.week_bounds import week_bounds
from planforge.services.week_view import assemble_week_view

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/today", response_model=TodayViewResponse)
def today_view_endpoint(
    session: Session = Depends(get_db),
    reference: date | None = Query(default=None, alias="date"),
) -> TodayViewResponse:
    """Return the Today view for a reference date."""
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    reference_date = (
        LocalDate.from_date(reference) if reference is not None else clock.today()
    )
    view = assemble_today_view(
        session=session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=reference_date,
        clock_today=clock.today(),
        policies=policies,
    )
    return TodayViewResponse.from_view(view)


@router.get("/week", response_model=WeekViewResponse)
def week_view_endpoint(
    session: Session = Depends(get_db),
    week_start_param: date | None = Query(default=None, alias="week_start"),
) -> WeekViewResponse:
    """Return the Week view for a week starting on the given date."""
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    today = clock.today()
    if week_start_param is not None:
        week_start, _ = week_bounds(
            reference_date=LocalDate.from_date(week_start_param),
            week_start_day=policies.week_start_day,
        )
    else:
        week_start, _ = week_bounds(
            reference_date=today,
            week_start_day=policies.week_start_day,
        )

    view = assemble_week_view(
        session=session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=policies,
    )
    return WeekViewResponse.from_view(view)


@router.get("/month", response_model=MonthViewResponse)
def month_view_endpoint(
    session: Session = Depends(get_db),
    month_param: str | None = Query(default=None, alias="month"),
) -> MonthViewResponse:
    """Return the Month view for a YYYY-MM calendar month."""
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    if month_param is not None:
        try:
            year_str, month_str = month_param.split("-", maxsplit=1)
            reference_date = LocalDate(int(year_str), int(month_str), 1)
        except (ValueError, InvalidLocalDateError) as exc:
            raise HTTPException(
                status_code=422,
                detail="month must be YYYY-MM",
            ) from exc
    else:
        reference_date = clock.today().start_of_month()

    view = assemble_month_view(
        session=session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=reference_date,
        clock_today=clock.today(),
        policies=policies,
    )
    return MonthViewResponse.from_view(view)
