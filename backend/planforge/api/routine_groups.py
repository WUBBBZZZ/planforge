"""Routine group API endpoints."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.api.routines import RoutineResponse
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.services import routine_group_service

router = APIRouter(prefix="/routine-groups", tags=["routine-groups"])


class RoutineGroupResponse(BaseModel):
    id: str
    name: str
    sort_order: int
    week_visible: bool
    is_system: bool

    @classmethod
    def from_group(cls, group) -> "RoutineGroupResponse":
        return cls(
            id=group.id,
            name=group.name,
            sort_order=group.sort_order,
            week_visible=group.week_visible,
            is_system=group.is_system,
        )


class RoutineGroupWithRoutinesResponse(RoutineGroupResponse):
    routines: list[RoutineResponse]


class RoutineGroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class RoutineGroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    week_visible: bool | None = None


class ReorderGroupsRequest(BaseModel):
    group_ids: list[str] = Field(min_length=1)


class ReorderRoutinesRequest(BaseModel):
    routine_ids: list[str] = Field(min_length=1)


class MoveRoutineRequest(BaseModel):
    group_id: str
    sort_order: int = Field(ge=0)


@router.get("", response_model=list[RoutineGroupResponse])
def list_groups_endpoint(session: Session = Depends(get_db)) -> list[RoutineGroupResponse]:
    groups = routine_group_service.list_groups(session, owner_id=LOCAL_OWNER_ID)
    return [RoutineGroupResponse.from_group(group) for group in groups]


@router.get("/board", response_model=list[RoutineGroupWithRoutinesResponse])
def grouped_routines_endpoint(
    session: Session = Depends(get_db),
) -> list[RoutineGroupWithRoutinesResponse]:
    grouped = routine_group_service.list_grouped_routines(
        session,
        owner_id=LOCAL_OWNER_ID,
    )
    return [
        RoutineGroupWithRoutinesResponse(
            id=group.id,
            name=group.name,
            sort_order=group.sort_order,
            week_visible=group.week_visible,
            is_system=group.is_system,
            routines=[RoutineResponse.from_routine(routine) for routine in routines],
        )
        for group, routines in grouped
    ]


@router.post("", response_model=RoutineGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group_endpoint(
    body: RoutineGroupCreateRequest,
    session: Session = Depends(get_db),
) -> RoutineGroupResponse:
    group = routine_group_service.create_group(
        session,
        owner_id=LOCAL_OWNER_ID,
        name=body.name,
    )
    session.commit()
    return RoutineGroupResponse.from_group(group)


@router.patch("/{group_id}", response_model=RoutineGroupResponse)
def update_group_endpoint(
    group_id: str,
    body: RoutineGroupUpdateRequest,
    session: Session = Depends(get_db),
) -> RoutineGroupResponse:
    group = routine_group_service.update_group(
        session,
        group_id=group_id,
        owner_id=LOCAL_OWNER_ID,
        name=body.name,
        week_visible=body.week_visible,
    )
    session.commit()
    return RoutineGroupResponse.from_group(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_endpoint(
    group_id: str,
    session: Session = Depends(get_db),
) -> None:
    routine_group_service.delete_group(
        session,
        group_id=group_id,
        owner_id=LOCAL_OWNER_ID,
    )
    session.commit()


@router.put("/reorder", response_model=list[RoutineGroupResponse])
def reorder_groups_endpoint(
    body: ReorderGroupsRequest,
    session: Session = Depends(get_db),
) -> list[RoutineGroupResponse]:
    groups = routine_group_service.reorder_groups(
        session,
        owner_id=LOCAL_OWNER_ID,
        ordered_group_ids=body.group_ids,
    )
    session.commit()
    return [RoutineGroupResponse.from_group(group) for group in groups]


@router.put("/{group_id}/routines/reorder", response_model=list[RoutineResponse])
def reorder_routines_endpoint(
    group_id: str,
    body: ReorderRoutinesRequest,
    session: Session = Depends(get_db),
) -> list[RoutineResponse]:
    routines = routine_group_service.reorder_routines_in_group(
        session,
        owner_id=LOCAL_OWNER_ID,
        group_id=group_id,
        ordered_routine_ids=body.routine_ids,
    )
    session.commit()
    return [RoutineResponse.from_routine(routine) for routine in routines]


@router.post("/routines/{routine_id}/move", response_model=RoutineResponse)
def move_routine_endpoint(
    routine_id: str,
    body: MoveRoutineRequest,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    routine = routine_group_service.move_routine(
        session,
        owner_id=LOCAL_OWNER_ID,
        routine_id=routine_id,
        group_id=body.group_id,
        sort_order=body.sort_order,
    )
    session.commit()
    return RoutineResponse.from_routine(routine)
