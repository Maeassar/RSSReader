from fastapi import APIRouter, Query

from app.repositories import repository

router = APIRouter()


@router.get("/llm/timeseries")
def llm_timeseries(
    range: str | None = Query(None),
    provider: str | None = Query(None),
    model: str | None = Query(None),
):
    return repository.stats_timeseries(range, provider, model)


@router.get("/llm")
def llm_stats(
    range: str | None = Query(None),
    provider: str | None = Query(None),
    model: str | None = Query(None),
):
    return repository.stats(range, provider, model)


@router.delete("/llm")
def delete_llm_stats(
    provider: str | None = Query(None),
    model: str | None = Query(None),
):
    deleted = repository.delete_stats(provider, model)
    return {"ok": True, "deleted": deleted}
