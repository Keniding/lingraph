"""
Modelo de datos del grafo de contactos (property graph).

Person  -> nodo
Relationship -> arista (permite multigrafo: dos personas pueden tener
                varias aristas de distinto tipo/contexto)
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column, JSON


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RelationshipType(str, Enum):
    COLEGA = "colega"
    AMIGO = "amigo"
    MENTOR = "mentor"
    CLIENTE = "cliente"
    COMUNIDAD = "comunidad"
    EDUCACION = "educacion"
    FAMILIA = "familia"


class InteractionFrequency(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    DESCONOCIDA = "desconocida"


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    nombre: str
    alias: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    empresa_actual: Optional[str] = None
    cargo: Optional[str] = None
    ubicacion: Optional[str] = None
    email: Optional[str] = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    fuentes: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    fecha_primer_contacto: Optional[date] = None
    fecha_ultimo_contacto: Optional[date] = None
    notas: Optional[str] = None

    # Modelo federado: si esta persona conectó su propia cuenta,
    # es owner de su propio subgrafo (no solo un nodo pasivo).
    es_owner: bool = False
    owner_user_id: Optional[UUID] = None
    linkedin_profile_url: Optional[str] = Field(default=None, index=True)
    # `sub` de OpenID Connect: id estable del miembro que autenticó.
    # Sirve para upsert del owner sin duplicar su nodo en cada login.
    linkedin_sub: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Relationship(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    origen_id: UUID = Field(foreign_key="person.id", index=True)
    destino_id: UUID = Field(foreign_key="person.id", index=True)

    tipo: RelationshipType
    contexto: Optional[str] = None  # ej: "AWS Student Builder Group Peru"
    fuerza: float = Field(default=0.0, ge=0.0, le=1.0)
    fecha_inicio: Optional[date] = None
    frecuencia_interaccion: InteractionFrequency = InteractionFrequency.DESCONOCIDA
    evidencia: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=_utcnow)
