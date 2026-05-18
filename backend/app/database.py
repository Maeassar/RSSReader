"""Reserved database wiring for the future SQLite implementation.

The current project stage intentionally uses in-memory repositories so the API
contract and Vue application can be developed before the SQLite schema exists.
When the database is ready, add the SQLAlchemy engine/session here and swap the
mock repositories for SQLAlchemy repositories without changing routers.
"""

DATABASE_URL = "sqlite:///./rssreader.db"


def get_db():
    raise NotImplementedError("SQLite is reserved for the next implementation stage.")

