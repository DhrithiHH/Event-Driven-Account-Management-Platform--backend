from sqlalchemy import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_sa_engine(url: str | URL) -> AsyncEngine:
    if isinstance(url, str):
        url_obj = make_url(url)
    else:
        url_obj = url

    connect_args = {}
    query_dict = dict(url_obj.query)
    ssl_req = query_dict.get("ssl") or query_dict.get("sslmode")
    if ssl_req in ("require", "required", "true", "True", "prefer"):
        connect_args["ssl"] = "require" if ssl_req != "prefer" else "prefer"
        cleaned_query = {
            k: v for k, v in query_dict.items() if k not in ("ssl", "sslmode")
        }
        url_obj = url_obj.set(query=cleaned_query)

    return create_async_engine(url_obj, connect_args=connect_args)


def create_sa_session_factory(
    engine: AsyncEngine, autoflush: bool = False, expire_on_commit: bool = False
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine, autoflush=autoflush, expire_on_commit=expire_on_commit
    )
