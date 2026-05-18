from app.repositories import repository


def list_tags():
    return repository.list_tags()


def create_tag(payload):
    return repository.create_tag(payload)


def update_tag(tag_id, payload):
    return repository.update_tag(tag_id, payload)


def delete_tag(tag_id):
    repository.delete_tag(tag_id)


def set_article_tags(article_id, tag_ids):
    return repository.set_article_tags(article_id, tag_ids)

