"""Tests del parser del export de LinkedIn."""
from app.services.linkedin_csv_parser import parse_linkedin_connections_csv

# Export real de LinkedIn: trae líneas de nota antes del header verdadero.
SAMPLE_CSV = (
    "Notes:\n"
    '"When exporting your connection data, you may notice that '
    "some of the fields are empty.\"\n"
    "\n"
    "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
    "Ada,Lovelace,https://www.linkedin.com/in/ada,ada@example.com,Analytical Engine,Mathematician,15 Mar 2024\n"
    "Alan,Turing,https://www.linkedin.com/in/alan,,Bletchley Park,Cryptanalyst,01 Jan 2023\n"
).encode("utf-8")


def test_parses_rows_after_note_header():
    conns = list(parse_linkedin_connections_csv(SAMPLE_CSV))
    assert len(conns) == 2

    ada = conns[0]
    assert ada.full_name == "Ada Lovelace"
    assert ada.profile_url == "https://www.linkedin.com/in/ada"
    assert ada.email == "ada@example.com"
    assert ada.company == "Analytical Engine"
    assert ada.connected_on is not None
    assert ada.connected_on.year == 2024


def test_empty_email_becomes_none():
    conns = list(parse_linkedin_connections_csv(SAMPLE_CSV))
    assert conns[1].email is None


def test_handles_utf8_bom():
    with_bom = b"\xef\xbb\xbf" + SAMPLE_CSV
    conns = list(parse_linkedin_connections_csv(with_bom))
    assert len(conns) == 2
