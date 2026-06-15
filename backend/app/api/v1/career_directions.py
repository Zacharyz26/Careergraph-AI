from fastapi import APIRouter

from app.schemas.career_direction import (
    CareerDirectionRequest,
    CareerDirectionResponse,
)
from app.services.career_direction_service import CareerDirectionService

router = APIRouter()
career_direction_service = CareerDirectionService()


@router.post("/recommend", response_model=CareerDirectionResponse)
async def recommend_career_directions(
    payload: CareerDirectionRequest,
) -> CareerDirectionResponse:
    return await career_direction_service.recommend(payload.candidate_profile)
