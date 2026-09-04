from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos la configuración de DB y los routers
from app.core.database import create_db_and_tables
from app.api import (
    routes_planes,
    routes_premios,
    routes_sorteos,
    routes_resultados,
    routes_tubos,
    routes_pre_sorteos,
    routes_auth,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Lotería del Risaralda API", lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
# NOTA: el regex acepta http:// o https:// para localhost (desarrollo usa
# http), y solo https:// para el dominio de Vercel (producción).
#
# allow_credentials=False: la sesión ya NO usa cookies (ver app/api/routes_auth.py
# y app/core/deps.py) — usa un JWT que el frontend manda como header
# Authorization: Bearer <token>. Se cambió de cookie a header porque el
# frontend (Vercel) y el backend (Render) son dominios raíz distintos, y
# los navegadores modernos bloquean por defecto las cookies "de terceros"
# entre sitios así, sin importar los ajustes de SameSite/Secure.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost:3000|(?:loteria-risaralda)(-git-[\w-]+-[\w]+)?\.vercel\.app)",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- INCLUSIÓN DE ROUTERS ---
app.include_router(routes_auth.router)  # <--- Nuevo router de autenticación
app.include_router(routes_planes.router)
app.include_router(routes_premios.router)
app.include_router(routes_sorteos.router)
app.include_router(routes_resultados.router)
app.include_router(routes_tubos.router)
app.include_router(routes_pre_sorteos.router)