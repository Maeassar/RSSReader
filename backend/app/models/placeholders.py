"""Model placeholders for the future SQLite implementation.

Keep these class names stable so SQLAlchemy models can be added later without
changing service or router naming.
"""


class Feed:
    pass


class Article:
    pass


class Tag:
    pass


class ArticleTag:
    pass


class Note:
    pass


class LLMProvider:
    pass


class AIResult:
    pass


class SyncLog:
    pass

