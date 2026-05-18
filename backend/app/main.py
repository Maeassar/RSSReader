from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, articles, export, feeds, logs, notes, opml, stats, tags

app = FastAPI(
    title="RSSReader API",
    description="Mock-first RSS reader API with reserved SQLite repository interfaces.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feeds.router, prefix="/api/feeds", tags=["feeds"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(opml.router, prefix="/api/opml", tags=["opml"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(notes.router, prefix="/api/articles", tags=["notes"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "storage": "mock", "database": "reserved"}

