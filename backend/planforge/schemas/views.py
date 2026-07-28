"""Pydantic schemas for planner views."""

from datetime import date

from planforge.domain.enums import ViewItemKind
from planforge.services.today_view import TodayItem, TodayView
from planforge.services.week_view import (
    WeekDayGroup,
    WeekItem,
    WeekTargetSummary,
    WeekView,
)
from planforge.services.month_view import MonthView
from pydantic import BaseModel


class TodayItemResponse(BaseModel):
    kind: ViewItemKind
    item_id: str
    title: str
    notes: str | None
    due_date: date | None
    starts_at: str | None
    ends_at: str | None
    is_overdue: bool
    routine_title: str | None = None
    is_completed: bool = False

    @classmethod
    def from_item(cls, item: TodayItem) -> TodayItemResponse:
        return cls(
            kind=item.kind,
            item_id=item.item_id,
            title=item.title,
            notes=item.notes,
            due_date=item.due_date.to_date() if item.due_date else None,
            starts_at=item.starts_at,
            ends_at=item.ends_at,
            is_overdue=item.is_overdue,
            routine_title=item.routine_title,
            is_completed=item.is_completed,
        )


class TodayViewResponse(BaseModel):
    reference_date: date
    items: list[TodayItemResponse]

    @classmethod
    def from_view(cls, view: TodayView) -> TodayViewResponse:
        return cls(
            reference_date=view.reference_date.to_date(),
            items=[TodayItemResponse.from_item(item) for item in view.items],
        )


class WeekItemResponse(BaseModel):
    kind: ViewItemKind
    item_id: str
    title: str
    due_date: date | None
    starts_at: str | None
    ends_at: str | None
    is_overdue: bool
    routine_title: str | None = None
    is_completed: bool = False

    @classmethod
    def from_item(cls, item: WeekItem) -> WeekItemResponse:
        return cls(
            kind=item.kind,
            item_id=item.item_id,
            title=item.title,
            due_date=item.due_date.to_date() if item.due_date else None,
            starts_at=item.starts_at,
            ends_at=item.ends_at,
            is_overdue=item.is_overdue,
            routine_title=item.routine_title,
            is_completed=item.is_completed,
        )


class WeekDayGroupResponse(BaseModel):
    date: date | None
    items: list[WeekItemResponse]
    label: str | None = None

    @classmethod
    def from_group(cls, group: WeekDayGroup) -> WeekDayGroupResponse:
        return cls(
            date=group.date.to_date() if group.date else None,
            items=[WeekItemResponse.from_item(item) for item in group.items],
            label=group.label,
        )


class WeekTargetSummaryResponse(BaseModel):
    target_id: str
    title: str
    completed_count: int
    target_count: int

    @classmethod
    def from_summary(cls, summary: WeekTargetSummary) -> WeekTargetSummaryResponse:
        return cls(
            target_id=summary.target_id,
            title=summary.title,
            completed_count=summary.completed_count,
            target_count=summary.target_count,
        )


class WeekViewResponse(BaseModel):
    week_start: date
    week_end: date
    days: list[WeekDayGroupResponse]
    targets: list[WeekTargetSummaryResponse]

    @classmethod
    def from_view(cls, view: WeekView) -> WeekViewResponse:
        return cls(
            week_start=view.week_start.to_date(),
            week_end=view.week_end.to_date(),
            days=[WeekDayGroupResponse.from_group(group) for group in view.days],
            targets=[
                WeekTargetSummaryResponse.from_summary(target)
                for target in view.targets
            ],
        )


class MonthViewResponse(BaseModel):
    month: str
    month_start: date
    month_end: date
    week_start_day: str
    days: list[WeekDayGroupResponse]

    @classmethod
    def from_view(cls, view: MonthView) -> MonthViewResponse:
        return cls(
            month=view.month,
            month_start=view.month_start.to_date(),
            month_end=view.month_end.to_date(),
            week_start_day=view.week_start_day,
            days=[WeekDayGroupResponse.from_group(group) for group in view.days],
        )
