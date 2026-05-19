from app.repositories import repository


def list_feeds():
    return repository.list_feeds()


def get_feed(feed_id):
    return repository.get_feed(feed_id)


def create_feed(payload):
    return repository.create_feed(payload)


def update_feed(feed_id, payload):
    return repository.update_feed(feed_id, payload)


def delete_feed(feed_id):
    repository.delete_feed(feed_id)


def sync_feed(feed_id):
    return repository.sync_feed(feed_id)


def sync_all_feeds():
    return [repository.sync_feed(feed["id"]) for feed in repository.list_feeds()]

