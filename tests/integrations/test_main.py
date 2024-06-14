import pytest
from fastapi.testclient import TestClient
from starlette import status

from tests.models import User

pytestmark = [pytest.mark.anyio]


async def test_main(
    http_client: TestClient,
    users: dict[str, dict[str, User]],
    root_user: User,
) -> None:
    """Main integration test."""
    # Check API structure (main route)

    assert users

    response = http_client.get(url="/admin/api/")
    assert response.status_code == status.HTTP_200_OK

    assert True
