# lingraph

Visualización del grafo de contactos propio a partir de LinkedIn:
quién se conecta con quién, cómo se agrupan tus círculos, y quién los
conecta entre sí.

## Decisiones de diseño

**Modelo de datos primero, visual después.** El core es un property
graph: nodos `Person` y aristas `Relationship` con propiedades libres
(tipo, contexto, fuerza, evidencia). Ver `backend/app/models/graph.py`.

**Fuente de datos: export manual CSV de LinkedIn, no scraping ni API
de conexiones.** LinkedIn no expone datos de conexiones por API para
casos no personales, y ni siquiera con aprobación de partner se puede
obtener el 2do grado (las conexiones de tus conexiones) — el techo es
el mismo que el export manual. El scraping viola los Términos de
Servicio y arriesga la cuenta. Por eso:

- `Sign in with LinkedIn` (OpenID Connect) se usa solo para **verificar
  identidad** de cada owner que se une (nombre, foto, email) —
  `backend/app/routers/auth.py`.
- Las conexiones reales entran subiendo el `Connections.csv` que cada
  persona descarga de su propia cuenta (Settings & Privacy > Get a copy
  of your data) — `backend/app/routers/imports.py`.

**Crecimiento federado, no exponencial por extracción.** El grafo
crece cuando cada contacto se une y sube su propio export, no
extrayendo los contactos de tus contactos. El campo `es_owner` en
`Person` distingue nodos pasivos (solo apareces en el grafo de alguien
más) de nodos activos (subiste tu propio export).

## Stack

- **Backend**: Python + FastAPI + SQLModel (SQLite en dev, Postgres en
  producción) + networkx para análisis de grafo (centralidad,
  comunidades).
- **Frontend** (pendiente): Cytoscape.js — buen balance entre
  exploración interactiva y algoritmos de análisis incluidos.

## Correr localmente

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Config: copia la plantilla y rellena tus valores (OAuth es opcional
# para levantar el server; sin él, /auth/linkedin/* responde 503).
cp .env.example .env

uvicorn app.main:app --reload
```

La API queda en http://127.0.0.1:8000 y la doc interactiva en `/docs`.

## Config

Las credenciales y la URL de la base salen de variables de entorno
(pydantic-settings), no del código. Ver `backend/.env.example`:

- `DATABASE_URL` — SQLite en dev, Postgres en prod.
- `SESSION_SECRET` — firma la cookie de sesión del flujo OAuth.
- `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` — de tu app en
  https://www.linkedin.com/developers/ (producto "Sign In with LinkedIn
  using OpenID Connect").

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Cubren el parser del CSV (header tras las líneas de nota, BOM, emails
vacíos) y un smoke test de la API (health, import y lectura del grafo)
con SQLite en memoria.

## Próximos pasos

- [x] Variables de entorno reales para OAuth de LinkedIn (client_id/secret)
- [ ] Endpoint de merge cuando dos owners reportan la misma arista
- [ ] Frontend con Cytoscape.js consumiendo `/graph/nodes` y `/graph/edges`
- [ ] Cálculo automático de `fuerza` de arista a partir de recencia/frecuencia
