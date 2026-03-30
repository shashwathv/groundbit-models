from fastapi import APIRouter, Request
from ..models.schemas import StatusResponse, HistroyRepsonse

router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request):
    store = request.app.state.store

    latest = store.get_latest()

    return StatusResponse(
        listening=store.listening,
        latest=latest
    )

@router.get("/history", response_model=HistroyRepsonse)
def get_history(request: Request):
    store = request.app.state.store

    events, total = store.get_history()

    return HistroyRepsonse(
        total=total,
        events=events
    )

