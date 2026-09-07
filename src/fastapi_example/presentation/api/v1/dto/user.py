from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import model_validator

from .base import BaseSchema


class CreateUserDTO(BaseSchema):
    username: str
    email: str
    password: str


class UserResponseDTO(BaseSchema):
    id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class UpdateUserDTO(BaseSchema):
    username: Optional[str] = None
    email: Optional[str] = None

    @model_validator(mode="after")
    def has_update_data(self) -> "UpdateUserDTO":
        if self.username is None and self.email is None:
            raise ValueError("At least one of username or email must be provided")
        return self


class DeleteUserDTO(BaseSchema):
    password: str
