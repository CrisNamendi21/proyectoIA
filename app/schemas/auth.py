from pydantic import BaseModel, Field, field_validator

from app.core.validation import normalize_username


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, repr=False)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return normalize_username(value) if isinstance(value, str) else value


class AuthenticatedUser(BaseModel):
    id: int = Field(gt=0)
    username: str = Field(min_length=1, max_length=50)


class LoginResponse(AuthenticatedUser):
    pass
