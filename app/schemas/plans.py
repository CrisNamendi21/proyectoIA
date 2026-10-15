import math
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


PositiveId = Annotated[int, Field(strict=True, gt=0)]


def validate_json_value(value: object) -> None:
    """Reject Python values that would be coerced or cannot be stored as JSON."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            validate_json_value(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            validate_json_value(item)
        return
    raise ValueError("El contenido debe contener exclusivamente valores JSON válidos")


class PlanningCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade_id: PositiveId | None = None
    subject_id: PositiveId | None = None
    curriculum_content_id: PositiveId | None = None
    content: dict[str, JsonValue]

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, value: object) -> object:
        if type(value) is not dict:
            raise ValueError("content debe ser un objeto JSON")
        validate_json_value(value)
        return value


class PlanningUpdate(PlanningCreate):
    # The default permits omission; the inherited validator rejects explicit null.
    content: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_changes(self) -> "PlanningUpdate":
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        return self


class PlanningRead(PlanningCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: PositiveId
    user_id: PositiveId
    created_at: datetime
    updated_at: datetime
