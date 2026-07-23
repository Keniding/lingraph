"""Smoke tests de la API: health, import de CSV y lectura del grafo.

Usa una base SQLite en memoria por test para no tocar lingraph.db.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.graph import Person

SAMPLE_CSV = (
    "Notes:\n"
    "\n"
    "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
    "Ada,Lovelace,https://www.linkedin.com/in/ada,ada@example.com,AE,Mathematician,15 Mar 2024\n"
).encode("utf-8")


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def _session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _session_override
    with TestClient(app) as c:
        yield c, engine
    app.dependency_overrides.clear()


def test_health(client):
    c, _ = client
    assert c.get("/health").json() == {"status": "ok"}


def test_import_csv_creates_nodes_and_edges(client):
    c, engine = client
    with Session(engine) as session:
        owner = Person(nombre="Yo", es_owner=True)
        session.add(owner)
        session.commit()
        owner_id = str(owner.id)

    resp = c.post(
        "/imports/linkedin-csv",
        params={"owner_person_id": owner_id},
        files={"file": ("Connections.csv", SAMPLE_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["personas_creadas"] == 1
    assert body["aristas_creadas"] == 1

    nodes = c.get("/graph/nodes").json()
    assert len(nodes) == 2  # owner + Ada
    edges = c.get("/graph/edges").json()
    assert len(edges) == 1


def test_import_unknown_owner_returns_404(client):
    c, _ = client
    resp = c.post(
        "/imports/linkedin-csv",
        params={"owner_person_id": "00000000-0000-0000-0000-000000000000"},
        files={"file": ("Connections.csv", SAMPLE_CSV, "text/csv")},
    )
    assert resp.status_code == 404
