import pytest

from httpx import AsyncClient
from myapp.models.task import TaskStatus

async def create_task(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/tasks/",
        json={"title": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()

async def update_task(
    id: int, payload: dict, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.patch(
        f"/tasks/{id}",
        json = payload,
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()

@pytest.fixture()
async def created_task(async_client: AsyncClient, logged_in_token: str):
    return await create_task("Test Task", async_client, logged_in_token)

@pytest.fixture()
async def updated_task_with_status(async_client: AsyncClient, logged_in_token: str, created_task: dict):
    payload = {"status": TaskStatus.IN_PROGRESS}
    return await update_task(created_task["id"],payload, async_client,logged_in_token)

@pytest.mark.anyio
async def test_create_task(
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

@pytest.mark.anyio
async def test_get_task(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token:str, created_task: dict
):    
    response = await async_client.get(
        "/tasks/" ,
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 200
    assert created_task.items() <= response.json()[0].items()


@pytest.mark.anyio
async def test_get_task_with_search(
        async_client: AsyncClient, confirmed_user:dict , logged_in_token:str,created_task: dict
):
    response = await async_client.get(
        "/tasks/",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"search": "Test"}
    )

    assert response.status_code == 200
    assert created_task.items() <= response.json()[0].items()

@pytest.mark.anyio
async def test_empty_get_task_with_search(
    async_client: AsyncClient, confirmed_user:dict , logged_in_token:str,created_task: dict
):
    response = await async_client.get(
        "/tasks/",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"search": "abc"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 0
    
@pytest.mark.anyio
async def test_patch_task_with_updated_status(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str, updated_task_with_status: dict
):
    response = await async_client.get(
        "/tasks/",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"status": TaskStatus.IN_PROGRESS}
    )

    assert response.status_code == 200
    assert updated_task_with_status.items() <= response.json()[0].items()


@pytest.mark.anyio
async def test_delete_task(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str, created_task: dict
):
    response = await async_client.delete(
        f"/tasks/{created_task['id']}",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 204