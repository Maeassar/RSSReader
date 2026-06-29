from app.repositories import repository
from app.schemas import FeedUpdate


def list_feeds():
    return repository.list_feeds()


def get_feed(feed_id):
    return repository.get_feed(feed_id)


def create_feed(payload):
    feed = repository.create_feed_metadata(payload)
    try:
        synced_feed = repository.sync_feed(feed["id"])
    except Exception as exc:
        return {
            "status": "partial",
            "message": str(exc),
            "feed": repository.get_feed(feed["id"]),
        }
    if payload.title:
        synced_feed = repository.update_feed(feed["id"], FeedUpdate(title=payload.title))

    return {
        "status": "success",
        "message": "Feed added and synced successfully.",
        "feed": synced_feed,
    }


def update_feed(feed_id, payload):
    return repository.update_feed(feed_id, payload)


def delete_feed(feed_id):
    repository.delete_feed(feed_id)


def delete_feeds(feed_ids):
    results = []
    seen_feed_ids = set()
    for feed_id in feed_ids:
        if feed_id in seen_feed_ids:
            results.append(
                {
                    "feed_id": feed_id,
                    "status": "skipped",
                    "message": "Duplicate feed id in request.",
                }
            )
            continue

        seen_feed_ids.add(feed_id)
        try:
            repository.delete_feed(feed_id)
        except ValueError as exc:
            results.append(
                {
                    "feed_id": feed_id,
                    "status": "failed",
                    "message": str(exc),
                }
            )
            continue

        results.append(
            {
                "feed_id": feed_id,
                "status": "success",
                "message": "Feed deleted.",
            }
        )

    return {
        "total": len(results),
        "success": sum(1 for item in results if item["status"] == "success"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "results": results,
    }


def sync_feed(feed_id):
    return repository.sync_feed(feed_id)


def sync_all_feeds():
    results = []
    for feed in repository.list_feeds():
        feed_id = feed["id"]
        try:
            synced_feed = repository.sync_feed(feed_id)
        except Exception as exc:
            results.append(
                {
                    "feed_id": feed_id,
                    "url": feed.get("url"),
                    "title": feed.get("title"),
                    "status": "failed",
                    "message": str(exc),
                    "feed": None,
                }
            )
            continue

        results.append(
            {
                "feed_id": synced_feed["id"],
                "url": synced_feed["url"],
                "title": synced_feed["title"],
                "status": "success",
                "message": "Feed synced successfully.",
                "feed": synced_feed,
            }
        )

    return {
        "total": len(results),
        "success": sum(1 for item in results if item["status"] == "success"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "results": results,
    }

