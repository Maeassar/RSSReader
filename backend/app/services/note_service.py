from app.repositories import repository


def get_note(article_id):
    return repository.get_note(article_id)


def update_note(article_id, payload):
    return repository.update_note(article_id, payload)

