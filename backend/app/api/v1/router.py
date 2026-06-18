from fastapi import APIRouter

from app.api.v1 import (
    analysis_jobs,
    career_directions,
    jobs,
    matches,
    resumes,
    suggestions,
)

api_router = APIRouter()
api_router.include_router(
    analysis_jobs.router,
    prefix="/analysis-jobs",
    tags=["analysis-jobs"],
)
api_router.include_router(
    career_directions.router,
    prefix="/career-directions",
    tags=["career-directions"],
)
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])
