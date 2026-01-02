import pytest

from httpx import AsyncClient

async def create_task(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/tasks/",
        json={"title": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()

@pytest.fixture()
async def created_task(async_client: AsyncClient, logged_in_token: str):
    return await create_task("Test Task", async_client, logged_in_token)

@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    body = "Test Task"

    response = await async_client.post(
        "/tasks/",
        json={"title": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "title": body,
        "owner_id": confirmed_user["id"]
    }.items() <= response.json().items()
