import asyncio
from fastapi import APIRouter
from api.schemas import PipelineResponse
from scheduler.jobs import run_daily_automation_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/run", response_model=PipelineResponse)
async def trigger_pipeline():
    try:
        await run_daily_automation_pipeline()
        return PipelineResponse(status="success", message="Pipeline cycle completed.")
    except Exception as e:
        return PipelineResponse(status="error", message=str(e))