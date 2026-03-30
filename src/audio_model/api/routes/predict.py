from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Request, HTTPException
import tempfile

from ..services.worker import run_inference

router = APIRouter()

@router.post("/predict")
async def predict(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded...")
    
    store = request.app.state.store
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty file...")
            
            temp.write(content)
            temp_path = temp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed - {e}")

    background_tasks.add_task(
        run_inference,
        temp_path,
        store
    )

    return {"status":"received"}