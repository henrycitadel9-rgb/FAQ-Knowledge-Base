from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", summary="List Tasks")
def list_tasks():
    """Return a minimal placeholder list of tasks."""
    return {"tasks": []}


@router.get("/dashboard", summary="Dashboard")
def dashboard():
    return {"total": 0, "by_status": {"todo": 0, "in_progress": 0, "done": 0}}
