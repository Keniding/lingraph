"""
Parser del export nativo de LinkedIn (Settings & Privacy > Get a copy of
your data > Connections).

El archivo Connections.csv trae unas líneas de nota antes del header real:
    First Name,Last Name,URL,Email Address,Company,Position,Connected On

Este parser detecta esa fila de header automáticamente en vez de asumir
que está en la línea 1 (LinkedIn cambia el número de líneas de nota
de tanto en tanto).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

EXPECTED_HEADER_PREFIX = "First Name"


@dataclass
class LinkedInConnection:
    first_name: str
    last_name: str
    profile_url: str | None
    email: str | None
    company: str | None
    position: str | None
    connected_on: datetime | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


def _find_header_row(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if line.startswith(EXPECTED_HEADER_PREFIX):
            return i
    raise ValueError(
        "No se encontró la fila de header del export de LinkedIn "
        "(se esperaba una fila que empiece con 'First Name')."
    )


def parse_linkedin_connections_csv(raw_bytes: bytes) -> Iterator[LinkedInConnection]:
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    header_idx = _find_header_row(lines)
    csv_content = "\n".join(lines[header_idx:])

    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        connected_on = None
        raw_date = (row.get("Connected On") or "").strip()
        if raw_date:
            try:
                # Formato de LinkedIn: "15 Mar 2024"
                connected_on = datetime.strptime(raw_date, "%d %b %Y")
            except ValueError:
                connected_on = None

        yield LinkedInConnection(
            first_name=(row.get("First Name") or "").strip(),
            last_name=(row.get("Last Name") or "").strip(),
            profile_url=(row.get("URL") or "").strip() or None,
            email=(row.get("Email Address") or "").strip() or None,
            company=(row.get("Company") or "").strip() or None,
            position=(row.get("Position") or "").strip() or None,
            connected_on=connected_on,
        )
