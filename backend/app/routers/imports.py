from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.models.graph import Person, Relationship, RelationshipType
from app.services.linkedin_csv_parser import parse_linkedin_connections_csv

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/linkedin-csv")
async def import_linkedin_csv(
    owner_person_id: UUID,
    file: UploadFile,
    session: Session = Depends(get_session),
):
    """
    Sube el Connections.csv exportado de LinkedIn y lo mergea al grafo.

    owner_person_id: el Person que representa al dueño de esta cuenta
    (para que las aristas creadas salgan desde su nodo).
    """
    owner = session.get(Person, owner_person_id)
    if owner is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe un Person con id {owner_person_id}.",
        )

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
        "personas_creadas": created,
        "personas_ya_existentes": matched,
        "aristas_creadas": edges,
    }
