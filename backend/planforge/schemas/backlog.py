"""Pydantic schemas for backlog items."""

from planforge.domain.enums import BacklogStatus
from planforge.models.backlog_item import BacklogItem
from pydantic import BaseModel, ConfigDict


class BacklogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    notes: str | None
    status: BacklogStatus
    promoted_entity_type: str | None
    promoted_entity_id: str | None
    source_entity_type: str | None
    source_entity_id: str | None

    @classmethod
    def from_item(cls, item: BacklogItem) -> BacklogItemResponse:
        return cls(
            id=item.id,
            title=item.title,
            notes=item.notes,
            status=item.backlog_status,
            promoted_entity_type=item.promoted_entity_type,
            promoted_entity_id=item.promoted_entity_id,
            source_entity_type=item.source_entity_type,
            source_entity_id=item.source_entity_id,
        )
