"""Pydantic schemas for planner views."""

from datetime import date

from planforge.services.today_view import TodayTaskItem, TodayView
from planforge.services.week_view import WeekDayGroup, WeekTaskItem, WeekView
from pydantic import BaseModel


class TodayTaskItemResponse(BaseModel):
    task_id: str
    title: str
    notes: str | None
    due_date: date | None
    is_overdue: bool

    @classmethod
    def from_item(cls, item: TodayTaskItem) -> TodayTaskItemResponse:
        return cls(
            task_id=item.task_id,
            title=item.title,
            notes=item.notes,
            due_date=item.due_date.to_date() if item.due_date else None,
            is_overdue=item.is_overdue,
        )


class TodayViewResponse(BaseModel):
    reference_date: date
    tasks: list[TodayTaskItemResponse]

    @classmethod
    def from_view(cls, view: TodayView) -> TodayViewResponse:
        return cls(
            reference_date=view.reference_date.to_date(),
            tasks=[TodayTaskItemResponse.from_item(item) for item in view.tasks],
        )


class WeekTaskItemResponse(BaseModel):
    task_id: str
    title: str
    due_date: date | None
    is_overdue: bool

    @classmethod
    def from_item(cls, item: WeekTaskItem) -> WeekTaskItemResponse:
        return cls(
            task_id=item.task_id,
            title=item.title,
            due_date=item.due_date.to_date() if item.due_date else None,
            is_overdue=item.is_overdue,
        )


class WeekDayGroupResponse(BaseModel):
    date: date | None
    tasks: list[WeekTaskItemResponse]

    @classmethod
    def from_group(cls, group: WeekDayGroup) -> WeekDayGroupResponse:
        return cls(
            date=group.date.to_date() if group.date else None,
            tasks=[WeekTaskItemResponse.from_item(item) for item in group.tasks],
        )


class WeekViewResponse(BaseModel):
    week_start: date
    week_end: date
    days: list[WeekDayGroupResponse]

    @classmethod
    def from_view(cls, view: WeekView) -> WeekViewResponse:
        return cls(
            week_start=view.week_start.to_date(),
            week_end=view.week_end.to_date(),
            days=[WeekDayGroupResponse.from_group(group) for group in view.days],
        )
