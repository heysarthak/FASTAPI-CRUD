from datetime import datetime
from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

# 1. Define an Enum for status to avoid "magic numbers"
class TaskStatus(IntEnum):
    TODO = 0
    IN_PROGRESS = 1
    DONE = 2

# 2. Shared fields (Base Model)
class TaskBase(BaseModel):
    title: str = Field(
        ..., 
        min_length=3, 
        max_length=100, 
        description="The title of the task",
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="0: Todo, 1: In Progress, 2: Done"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="The deadline for the task"
    )

# 3. Model for creating a task (Input from user)
class TaskCreate(TaskBase):
    pass  # Usually, the user only sends title, status, and end_date

# 4. Model for updating a task (Partial updates)
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    status: Optional[TaskStatus] = None
    end_date: Optional[datetime] = None

# 5. Full Task model (Output to user/Response)
class Task(TaskBase):
    id: int
    owner_id: int
    
    # Modern Pydantic V2 configuration
    model_config = ConfigDict(
        from_attributes=True,      # Link SQLAlchemy objects
        str_strip_whitespace=True, # Auto-trim titles
        use_enum_values=True       # Return '0' instead of 'TaskStatus.TODO' in JSON
    )