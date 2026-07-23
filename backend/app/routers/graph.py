from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.graph import Person, Relationship
from app.services.graph_service import detect_communities, top_connectors

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/nodes")
def list_nodes(session: Session = Depends(get_session)):
    return session.exec(select(Person)).all()


@router.get("/edges")
def list_edges(session: Session = Depends(get_session)):
    return session.exec(select(Relationship)).all()


@router.get("/analysis/top-connectors")
def get_top_connectors(session: Session = Depends(get_session)):
    """Quiénes conectan tus círculos distintos entre sí (betweenness)."""
    return [{"person_id": pid, "score": score} for pid, score in top_connectors(session)]


@router.get("/analysis/communities")
def get_communities(session: Session = Depends(get_session)):
    return [list(c) for c in detect_communities(session)]
