from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


PreferredLanguage = Literal["en", "zh"]


class ProcessingState(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(APIModel):
    resource_id: UUID
    state: ProcessingState
    message: str | None = None
    updated_at: datetime
