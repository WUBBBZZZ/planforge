"""Settings API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.services.settings_service import (
    DEFAULT_SETTINGS,
    get_settings_map,
    update_setting,
)

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    settings: dict[str, str]


class SettingUpdateRequest(BaseModel):
    value: str


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(session: Session = Depends(get_db)) -> SettingsResponse:
    settings = get_settings_map(session, owner_id=LOCAL_OWNER_ID)
    return SettingsResponse(settings=settings)


@router.patch("/{key}", response_model=SettingsResponse)
def update_setting_endpoint(
    key: str,
    body: SettingUpdateRequest,
    session: Session = Depends(get_db),
) -> SettingsResponse:
    if key not in DEFAULT_SETTINGS:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=f"Unknown setting key: {key}")
    try:
        update_setting(
            session,
            owner_id=LOCAL_OWNER_ID,
            key=key,
            value=body.value,
        )
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(exc)) from exc
    settings = get_settings_map(session, owner_id=LOCAL_OWNER_ID)
    return SettingsResponse(settings=settings)
