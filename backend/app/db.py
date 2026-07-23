from sqlmodel import SQLModel, Session, create_engine

from app.config import get_settings

# La URL sale de la config (variable de entorno DATABASE_URL). SQLite en
# dev; en prod, una URL de Postgres. connect_args solo aplica a SQLite.
_url = get_settings().database_url
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, echo=False, connect_args=_connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
