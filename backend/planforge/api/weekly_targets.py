"""Weekly target API endpoints."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import WeeklyTargetStatus
from planforge.models.weekly_target import WeeklyTarget
from planforge.services import weekly_target_service

router = APIRouter(prefix="/weekly-targets", tags=["weekly-targets"])


class WeeklyTargetCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    target_count: int = Field(default=1, ge=1)


class WeeklyTargetUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    target_count: int | None = Field(default=None, ge=1)


class WeeklyTargetResponse(BaseModel):
    id: str
    title: str
    target_count: int
    status: WeeklyTargetStatus

    @classmethod
    def from_target(cls, target: WeeklyTarget) -> WeeklyTargetResponse:
        return cls(
            id=target.id,
            title=target.title,
            target_count=target.target_count,
            status=target.target_status,
        )


@router.get("", response_model=list[WeeklyTargetResponse])
def list_weekly_targets_endpoint(
    session: Session = Depends(get_db),
) -> list[WeeklyTargetResponse]:
    targets = weekly_target_service.list_weekly_targets(
        session,
        owner_id=LOCAL_OWNER_ID,
    )
    return [WeeklyTargetResponse.from_target(target) for target in targets]


@router.post(
    "",
    response_model=WeeklyTargetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_weekly_target_endpoint(
    body: WeeklyTargetCreateRequest,
    session: Session = Depends(get_db),
) -> WeeklyTargetResponse:
    target = weekly_target_service.create_weekly_target(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        target_count=body.target_count,
    )
    return WeeklyTargetResponse.from_target(target)


@router.patch("/{target_id}", response_model=WeeklyTargetResponse)
def update_weekly_target_endpoint(
    target_id: str,
    body: WeeklyTargetUpdateRequest,
    session: Session = Depends(get_db),
) -> WeeklyTargetResponse:
    target = weekly_target_service.update_weekly_target(
        session,
        target_id=target_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        target_count=body.target_count,
    )
    return WeeklyTargetResponse.from_target(target)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weekly_target_endpoint(
    target_id: str,
    session: Session = Depends(get_db),
) -> None:
    weekly_target_service.delete_weekly_target(
        session,
        target_id=target_id,
        owner_id=LOCAL_OWNER_ID,
    )


@router.post("/{target_id}/progress", response_model=WeeklyTargetResponse)
def log_target_progress_endpoint(
    target_id: str,
    session: Session = Depends(get_db),
) -> WeeklyTargetResponse:
    target = weekly_target_service.log_target_progress(
        session,
        target_id=target_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return WeeklyTargetResponse.from_target(target)
