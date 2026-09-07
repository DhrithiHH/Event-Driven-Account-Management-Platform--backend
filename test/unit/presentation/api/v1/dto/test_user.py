import pytest
from pydantic import ValidationError

from fastapi_example.presentation.api.v1.dto import UpdateUserDTO


def test_update_user_dto_rejects_empty_payload() -> None:
    with pytest.raises(ValidationError, match="At least one of username or email"):
        UpdateUserDTO()


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "new_name"},
        {"email": "new@email.com"},
        {"username": "new_name", "email": "new@email.com"},
    ],
)
def test_update_user_dto_accepts_non_empty_payload(payload: dict[str, str]) -> None:
    dto = UpdateUserDTO(**payload)

    assert dto.model_dump(exclude_none=True) == payload
