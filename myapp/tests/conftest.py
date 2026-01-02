import os
from typing import AsyncGenerator, Generator
#from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient,ASGITransport

os.environ["ENV_STATE"] = "test"
from myapp.database import database, user_table, tasks as task_table  # noqa: E402
from myapp.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db():
    # If the app lifespan hasn't connected yet, we do it here
    if not database.is_connected:
        await database.connect()
    yield
    # We leave it connected for the app to use, 
    # or disconnect if it's the end of the test.
    if database.is_connected:
        await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    # Use transport instead of app for newer HTTPX versions
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url=client.base_url
    ) as ac:
        yield ac

@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details

@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update().where(user_table.c.email == registered_user["email"]).values(confirmed=True)
    )
    await database.execute(query)
    return registered_user

@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    # OAuth2PasswordRequestForm expects form data, not JSON
    # It also specifically looks for 'username' and 'password'
    login_data = {
        "username": confirmed_user["email"], 
        "password": confirmed_user["password"]
    }
    
    response = await async_client.post("/token", data=login_data) # Use 'data=' for form-encoding
    
    # Check if the request was successful to avoid cryptic KeyErrors
    assert response.status_code == 200, f"Login failed: {response.json()}"
    
    return response.json()["access_token"]

@pytest.fixture(autouse=True)
async def clear_db():
    # This runs BEFORE the test
    yield
    # This runs AFTER the test finishes
    await database.execute(user_table.delete())
    await database.execute(task_table.delete())
    # await database.execute(task_table.delete())
