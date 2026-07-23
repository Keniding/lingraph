"""
Sign in with LinkedIn (OpenID Connect).

IMPORTANTE: esto solo verifica identidad (nombre, foto, email) del
owner que se une al grafo. LinkedIn NO expone su lista de conexiones
por API ni para el propio usuario sin aprobación de partner, así que
las conexiones siguen entrando por /imports/linkedin-csv, no por acá.

Las credenciales salen de variables de entorno (ver app/config.py y
.env.example), no del código. Si no están configuradas, los endpoints
devuelven 503 en vez de romper al arrancar.
"""
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()

oauth = OAuth()
if _settings.linkedin_oauth_configured:
    oauth.register(
        name="linkedin",
        client_id=_settings.linkedin_client_id,
        client_secret=_settings.linkedin_client_secret,
        server_metadata_url="https://www.linkedin.com/oauth/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )


def _require_oauth() -> None:
    if not _settings.linkedin_oauth_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "LinkedIn OAuth no está configurado. Define LINKEDIN_CLIENT_ID "
                "y LINKEDIN_CLIENT_SECRET (ver .env.example)."
            ),
        )


@router.get("/linkedin/login")
async def linkedin_login(request: Request):
    _require_oauth()
    redirect_uri = request.url_for("linkedin_callback")
    return await oauth.linkedin.authorize_redirect(request, redirect_uri)


@router.get("/linkedin/callback", name="linkedin_callback")
async def linkedin_callback(request: Request):
    _require_oauth()
    token = await oauth.linkedin.authorize_access_token(request)
    userinfo = token.get("userinfo")  # nombre, email, foto — nada de conexiones
    return {"userinfo": userinfo}
