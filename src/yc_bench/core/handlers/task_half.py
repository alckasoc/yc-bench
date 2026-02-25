"""Handler for task_half_progress events."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from ...db.models.event import SimEvent
from ...db.models.task import Task


@dataclass
class TaskHalfResult:
    task_id: UUID
    handled: bool


def handle_task_half(db: Session, event: SimEvent) -> TaskHalfResult:
    """Mark the task's halfway_event_emitted flag as True."""
    task_id = UUID(event.payload["task_id"])
    task = db.query(Task).filter(Task.id == task_id).one_or_none()

    if task is None:
        return TaskHalfResult(task_id=task_id, handled=False)

    task.halfway_event_emitted = True
    db.flush()

    return TaskHalfResult(task_id=task_id, handled=True)
