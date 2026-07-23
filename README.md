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

Instalar y levantar (una vez):

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Con eso ya funciona todo lo del grafo. El `.env` (credenciales OAuth) es
**opcional**: solo hace falta si vas a usar el login con LinkedIn.

Tres URLs:

- http://127.0.0.1:8000/ui — **el visor del grafo** (lo que quieres ver).
- http://127.0.0.1:8000/docs — API interactiva (subir el CSV con botones).
- http://127.0.0.1:8000/health — chequeo rápido de que está vivo.

## Probarlo (sin OAuth, sin curl, todo en el visor)

1. Abre http://127.0.0.1:8000/ui
2. Arriba: escribe tu nombre, **Elegir CSV…**, selecciona tu
   `Connections.csv`, y **Importar**. El grafo se dibuja solo.
3. Botón *Top conectores* dimensiona los nodos puente; click en un nodo
   aísla su vecindario.

El visor recuerda tu `owner_person_id` (localStorage), así que si subes
otro CSV después, los contactos se suman al mismo nodo owner en vez de
crear uno nuevo. (También puedes importar vía `/docs` → `POST
/imports/linkedin-csv` si prefieres.)

> Si cambias el modelo de datos durante el desarrollo (agregar/quitar
> campos), borra `backend/lingraph.db` y reinicia: SQLite no migra tablas
> existentes solo, y consultar una columna que falta da error 500.
> `del backend\lingraph.db` (Windows) · `rm backend/lingraph.db` (Unix).

## Frontend

`/ui` sirve una página estática (`backend/app/static/index.html`) que
consume `/graph/nodes`, `/graph/edges` y `/graph/analysis/top-connectors`
y dibuja el grafo con Cytoscape.js:

- Nodos owner (`es_owner`) en verde, contactos en azul.
- Botón "Top conectores" — dimensiona los nodos por betweenness (quiénes
  hacen de puente entre tus círculos).
- Click en un nodo resalta su vecindario.

Cytoscape se carga por CDN; para uso offline, descarga el `.js` y sírvelo
local. Es un MVP embebido en el backend — más adelante puede migrar a un
SPA separado sin cambiar la API.

## Config

Las credenciales y la URL de la base salen de variables de entorno
(pydantic-settings), no del código. Ver `backend/.env.example`:

- `DATABASE_URL` — SQLite en dev, Postgres en prod.
- `SESSION_SECRET` — firma la cookie de sesión del flujo OAuth.
- `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` — de tu app en
  https://www.linkedin.com/developers/ (producto "Sign In with LinkedIn
  using OpenID Connect").

## Flujo de dos pasos (identidad + red)

1. **Identidad** — el owner entra por `GET /auth/linkedin/login` (Sign in
   with LinkedIn / OpenID Connect). El callback crea/actualiza su nodo
   `Person` con `es_owner=True` y devuelve su `owner_person_id`. Es
   idempotente por el `sub` de OIDC: iniciar sesión varias veces no
   duplica el nodo.
2. **Red** — con ese `owner_person_id`, el owner sube su `Connections.csv`
   a `POST /imports/linkedin-csv`. Las aristas creadas salen de su nodo.

LinkedIn nunca expone las conexiones por API, así que el paso 2 siempre es
upload manual — el OAuth del paso 1 es solo verificación de identidad.

### Configurar la app de LinkedIn

En https://www.linkedin.com/developers/ → Create app, y luego:

- Producto: **"Sign In with LinkedIn using OpenID Connect"** (self-serve).
- Tab Auth → Authorized redirect URL:
  `http://127.0.0.1:8000/auth/linkedin/callback`.
- Copia `Client ID` / `Client Secret` al `.env`.

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
- [x] Frontend con Cytoscape.js consumiendo `/graph/nodes` y `/graph/edges`
- [ ] Endpoint de merge cuando dos owners reportan la misma arista
- [ ] Cálculo automático de `fuerza` de arista a partir de recencia/frecuencia
