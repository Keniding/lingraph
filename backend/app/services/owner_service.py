"""
Upsert del `Person` owner a partir del userinfo de "Sign in with LinkedIn".

Enlaza el paso 1 (identidad OAuth) con el paso 2 (upload del CSV): cuando
alguien inicia sesión, aseguramos que exista su nodo owner (es_owner=True)
y devolvemos su id, que es el `owner_person_id` que luego usa el import.

Idempotente por `sub` (id estable de OpenID Connect): iniciar sesión N
veces no duplica el nodo, solo refresca sus datos.
"""
from __future__ import annotations

from sqlmodel import Session, select

from app.models.graph import Person, _utcnow


def upsert_owner_from_userinfo(session: Session, userinfo: dict) -> Person:
    sub = userinfo.get("sub")
    if not sub:
        raise ValueError("userinfo sin 'sub': no se puede identificar al owner.")

    nombre = userinfo.get("name") or (
        f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip()
    )

    person = session.exec(
        select(Person).where(Person.linkedin_sub == sub)
    ).first()

    if person is None:
        person = Person(linkedin_sub=sub, fuentes=["linkedin_oauth"])
        session.add(person)

    if nombre:
        person.nombre = nombre
    if userinfo.get("email"):
        person.email = userinfo["email"]
    person.es_owner = True
    if "linkedin_oauth" not in person.fuentes:
        person.fuentes = [*person.fuentes, "linkedin_oauth"]
    person.updated_at = _utcnow()

    session.commit()
    session.refresh(person)
    return person
