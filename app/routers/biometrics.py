from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.async_engine import get_async_db
from app.models.biometrics import SessionPayload
from app.services.process_session import process_session

router = APIRouter(prefix="/biometrics", tags=["Biometrics"])

@router.post("/process", status_code=202)
async def process_biometric_session(
    payload: SessionPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    if not payload.tasks:
        raise HTTPException(400, "tasks list empty")
    background_tasks.add_task(process_session, payload, db)
    return {"detail": "accepted"}

