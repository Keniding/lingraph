from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.models.graph import Person, Relationship, RelationshipType
from app.services.linkedin_csv_parser import parse_linkedin_connections_csv

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/linkedin-csv")
async def import_linkedin_csv(
    file: UploadFile,
    owner_person_id: Optional[str] = None,
    owner_name: str = "Yo",
    session: Session = Depends(get_session),
):
    """
    Sube el Connections.csv exportado de LinkedIn y lo mergea al grafo.

    - owner_person_id: el Person dueño de esta cuenta, para que las aristas
      salgan de su nodo. Normalmente lo obtienes del login OAuth.
    - Si no pasas owner_person_id, se crea un owner nuevo con `owner_name`
      (útil para probar en local sin OAuth). El id creado sale en la
      respuesta para que lo reutilices en el próximo import.

    Se recibe como texto (no UUID estricto) para tolerar valores vacíos o
    "undefined" que un cliente web puede mandar: se tratan como "sin owner".
    """
    owner_id = (owner_person_id or "").strip()
    if owner_id.lower() in ("", "undefined", "null", "none"):
        owner_id = None

    if owner_id is not None:
        try:
            owner_uuid = UUID(owner_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"owner_person_id no es un UUID válido: {owner_id!r}.",
            )
        owner = session.get(Person, owner_uuid)
        if owner is None:
            raise HTTPException(
                status_code=404,
                detail=f"No existe un Person con id {owner_id}.",
            )
    else:
        owner = Person(nombre=owner_name, es_owner=True, fuentes=["manual"])
        session.add(owner)
        session.flush()

    raw = await file.read()
    created, matched, edges = 0, 0, 0

    for conn in parse_linkedin_connections_csv(raw):
        existing = None
        if conn.profile_url:
            existing = session.exec(
                select(Person).where(Person.linkedin_profile_url == conn.profile_url)
            ).first()

        if existing:
            matched += 1
            person = existing
        else:
            person = Person(
                nombre=conn.full_name,
                empresa_actual=conn.company,
                cargo=conn.position,
                linkedin_profile_url=conn.profile_url,
                fuentes=["linkedin"],
                fecha_primer_contacto=conn.connected_on.date() if conn.connected_on else None,
            )
            session.add(person)
            session.flush()  # para obtener person.id antes del commit
            created += 1

        # Evita auto-aristas si el propio owner aparece en su export.
        if person.id == owner.id:
            continue

        session.add(
            Relationship(
                origen_id=owner.id,
                destino_id=person.id,
                tipo=RelationshipType.COLEGA,
                contexto="linkedin",
                evidencia=["linkedin_csv_export"],
            )
        )
        edges += 1

    session.commit()
    return {
        "owner_person_id": str(owner.id),
        "personas_creadas": created,
        "personas_ya_existentes": matched,
        "aristas_creadas": edges,
    }
