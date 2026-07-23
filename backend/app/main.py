from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import auth, graph, imports

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="lingraph", version="0.1.0", lifespan=lifespan)

# Necesario para el flujo OAuth de Authlib (guarda el state/nonce en la
# cookie de sesión firmada). La clave sale de la config.
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret)

app.include_router(auth.router)
app.include_router(imports.router)
app.include_router(graph.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Frontend estático (Cytoscape.js). Visualiza el grafo en /ui. Consume la
# misma API (/graph/nodes, /graph/edges, /graph/analysis/*), así que no
# necesita CORS al servirse desde el mismo origen.
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
