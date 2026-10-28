from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

import repository

app = FastAPI()

# Create table + seed on boot (same first-run rule as A2)
repository.init_db()


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


def not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@app.get("/tasks")
def get_tasks():
    return repository.list_tasks()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = repository.get_task(task_id)
    if task is None:
        raise not_found()
    return task


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required"
        )
    return repository.create_task(task.title.strip())


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    updated = repository.update_task(task_id, task.title, task.done)
    if updated is None:
        raise not_found()
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if not repository.delete_task(task_id):
        raise not_found()
    return None
