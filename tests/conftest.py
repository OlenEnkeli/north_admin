import pytest

pytest_plugins = [
    "anyio",
]

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
