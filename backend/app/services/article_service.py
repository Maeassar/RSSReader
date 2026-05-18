from app.repositories import repository


def list_articles(feed_id=None, tag_id=None, unread=None, starred=None):
    return repository.list_articles(feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)


def get_article(article_id):
    return repository.get_article(article_id)


def mark_read(article_id, is_read):
    return repository.set_article_flag(article_id, "is_read", is_read)


def mark_starred(article_id, is_starred):
    return repository.set_article_flag(article_id, "is_starred", is_starred)

