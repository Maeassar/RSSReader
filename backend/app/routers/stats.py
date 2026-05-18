from fastapi import APIRouter

from app.repositories import repository

router = APIRouter()


@router.get("/llm")
def llm_stats():
    return repository.stats()

