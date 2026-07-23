"""Tests del upsert del owner a partir del userinfo de OpenID Connect."""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.services.owner_service import upsert_owner_from_userinfo


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


USERINFO = {
    "sub": "abc123",
    "name": "Ada Lovelace",
    "email": "ada@example.com",
}


def test_creates_owner_node(session):
    owner = upsert_owner_from_userinfo(session, USERINFO)
    assert owner.es_owner is True
    assert owner.nombre == "Ada Lovelace"
    assert owner.email == "ada@example.com"
    assert "linkedin_oauth" in owner.fuentes


def test_upsert_is_idempotent_by_sub(session):
    first = upsert_owner_from_userinfo(session, USERINFO)
    # Segundo login del mismo miembro con nombre actualizado.
    second = upsert_owner_from_userinfo(
        session, {**USERINFO, "name": "Ada L. Byron"}
    )
    assert first.id == second.id
    assert second.nombre == "Ada L. Byron"
    # No debe acumular la fuente repetida.
    assert second.fuentes.count("linkedin_oauth") == 1


def test_missing_sub_raises(session):
    with pytest.raises(ValueError):
        upsert_owner_from_userinfo(session, {"name": "No Sub"})
