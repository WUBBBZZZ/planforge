"""Packing list API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.schemas.packing_list import (
    PackingEntryCreateRequest,
    PackingEntryUpdateRequest,
    PackingListCreateRequest,
    PackingListDetailResponse,
    PackingListEntryResponse,
    PackingListSummaryResponse,
    PackingListUpdateRequest,
)
from planforge.services import packing_list_service

router = APIRouter(prefix="/packing-lists", tags=["packing-lists"])


@router.get("", response_model=list[PackingListSummaryResponse])
def list_packing_lists_endpoint(
    session: Session = Depends(get_db),
) -> list[PackingListSummaryResponse]:
    lists = packing_list_service.list_packing_lists(session, owner_id=LOCAL_OWNER_ID)
    return [PackingListSummaryResponse.from_list(packing_list) for packing_list in lists]


@router.post(
    "",
    response_model=PackingListDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_packing_list_endpoint(
    body: PackingListCreateRequest,
    session: Session = Depends(get_db),
) -> PackingListDetailResponse:
    packing_list = packing_list_service.create_packing_list(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
    )
    detail = packing_list_service.get_packing_list(
        session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
    )
    return PackingListDetailResponse.from_list(detail)


@router.get("/{list_id}", response_model=PackingListDetailResponse)
def get_packing_list_endpoint(
    list_id: str,
    session: Session = Depends(get_db),
) -> PackingListDetailResponse:
    packing_list = packing_list_service.get_packing_list(
        session,
        list_id=list_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return PackingListDetailResponse.from_list(packing_list)


@router.patch("/{list_id}", response_model=PackingListDetailResponse)
def update_packing_list_endpoint(
    list_id: str,
    body: PackingListUpdateRequest,
    session: Session = Depends(get_db),
) -> PackingListDetailResponse:
    packing_list = packing_list_service.update_packing_list(
        session,
        list_id=list_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
    )
    return PackingListDetailResponse.from_list(packing_list)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_packing_list_endpoint(
    list_id: str,
    session: Session = Depends(get_db),
) -> None:
    packing_list_service.delete_packing_list(
        session,
        list_id=list_id,
        owner_id=LOCAL_OWNER_ID,
    )


@router.post(
    "/{list_id}/entries",
    response_model=PackingListEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_entry_endpoint(
    list_id: str,
    body: PackingEntryCreateRequest,
    session: Session = Depends(get_db),
) -> PackingListEntryResponse:
    entry = packing_list_service.create_entry(
        session,
        list_id=list_id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=body.entry_type,
        title=body.title,
    )
    return PackingListEntryResponse.from_entry(entry)


@router.patch("/entries/{entry_id}", response_model=PackingListEntryResponse)
def update_entry_endpoint(
    entry_id: str,
    body: PackingEntryUpdateRequest,
    session: Session = Depends(get_db),
) -> PackingListEntryResponse:
    entry = packing_list_service.update_entry(
        session,
        entry_id=entry_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        is_checked=body.is_checked,
        answer=body.answer,
        clear_answer=body.clear_answer,
    )
    return PackingListEntryResponse.from_entry(entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry_endpoint(
    entry_id: str,
    session: Session = Depends(get_db),
) -> None:
    packing_list_service.delete_entry(
        session,
        entry_id=entry_id,
        owner_id=LOCAL_OWNER_ID,
    )
