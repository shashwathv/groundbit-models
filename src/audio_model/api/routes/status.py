# routes/status.py

from fastapi import APIRouter, Request
from ..models.schemas import StatusResponse, HistoryResponse

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request):
    """
    Polled every 4 seconds by dashboard topbar.
    Returns: listening, latest detection, latest soil reading.
    Dashboard spec: soil.moisture_pct (not moisture).
    """
    store = request.app.state.store

    return StatusResponse(
        listening=store.listening,
        latest=store.get_latest(),
        soil=store.get_soil()
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(request: Request):
    """
    Returns last 100 detection events, newest first.
    total = lifetime count (survives deque trimming).
    Dashboard polls this for the event log table.
    """
    store  = request.app.state.store
    events, total = store.get_history()

    return HistoryResponse(
        total=total,
        events=events
    )