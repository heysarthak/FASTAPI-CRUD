from fastapi import APIRouter, Depends, Query,HTTPException,status
from database import tasks, database
from security import get_current_user
from models.task import TaskCreate, TaskUpdate, Task, TaskStatus
from typing import List, Optional

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current_user: dict = Depends(get_current_user)):
    query = tasks.insert().values(
        **payload.model_dump(), 
        owner_id=current_user["id"]
    )
    last_record_id = await database.execute(query)
    return {**payload.model_dump(), "id": last_record_id, "owner_id": current_user["id"]}

@router.get("/", response_model=List[Task])
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, min_length=1, description="Search tasks by title"),
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    # 1. Base query: Always restricted to the current user
    query = tasks.select().where(tasks.c.owner_id == current_user["id"])
    
    # 2. Search Logic (Case-insensitive title search)
    if search:
        # ilike allows "Work" to match "work", "WORK", etc.
        # The f"%{search}%" handles partial matches (e.g., "gro" matches "grocery")
        query = query.where(tasks.c.title.ilike(f"%{search}%"))
    
    # 3. Status Filter Logic
    if status_filter is not None:
        query = query.where(tasks.c.status == status_filter)
    
    # 4. Pagination (Always last)
    query = query.limit(limit).offset(offset)
    
    return await database.fetch_all(query)

@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: int, 
    payload: TaskUpdate, 
    current_user: dict = Depends(get_current_user)
):
    # Verify ownership and existence
    check_query = tasks.select().where(tasks.c.id == task_id).where(tasks.c.owner_id == current_user["id"])
    existing_task = await database.fetch_one(check_query)
    
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    update_query = tasks.update().where(tasks.c.id == task_id).values(**update_data)
    await database.execute(update_query)
    
    # Return the refreshed record
    return await database.fetch_one(check_query)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    # The WHERE clause includes owner_id to prevent users from deleting others' tasks
    query = tasks.delete().where(tasks.c.id == task_id).where(tasks.c.owner_id == current_user["id"])
    
    result = await database.execute(query)
    
    # result returns the number of rows deleted. If 0, it means the ID didn't exist for that user.
    if result == 0:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
    
    return None # 204 status code returns no body