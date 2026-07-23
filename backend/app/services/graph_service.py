"""
Wrapper sobre networkx para construir el grafo en memoria a partir de
Person/Relationship y exponer análisis (centralidad, comunidades, etc).

No reemplaza la base de datos relacional: SQLModel/SQLite (o Postgres
más adelante) sigue siendo la fuente de verdad. networkx se usa como
capa de análisis sobre esos datos, no de almacenamiento.
"""
from __future__ import annotations

import networkx as nx
from sqlmodel import Session, select

from app.models.graph import Person, Relationship


def build_graph(session: Session) -> nx.MultiDiGraph:
    """Reconstruye el grafo completo en memoria. Multigrafo porque dos
    personas pueden tener varias aristas de distinto tipo."""
    graph = nx.MultiDiGraph()

    for person in session.exec(select(Person)).all():
        graph.add_node(str(person.id), **person.model_dump(mode="json"))

    for rel in session.exec(select(Relationship)).all():
        graph.add_edge(
            str(rel.origen_id),
            str(rel.destino_id),
            key=str(rel.id),
            tipo=rel.tipo,
            fuerza=rel.fuerza,
            contexto=rel.contexto,
        )

    return graph


def top_connectors(session: Session, n: int = 10) -> list[tuple[str, float]]:
    """Centralidad de intermediación: quiénes conectan círculos distintos
    (ej: puente entre Interbank y Connect Technologies Community)."""
    graph = build_graph(session)
    undirected = graph.to_undirected()
    scores = nx.betweenness_centrality(undirected, weight=None)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:n]


def detect_communities(session: Session) -> list[set[str]]:
    """Detección de comunidades (círculos que se agrupan naturalmente)."""
    graph = build_graph(session).to_undirected()
    return list(nx.community.louvain_communities(graph, weight=None))
