from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routes import auth, admin, documentos, catalogo
from app.api import ejemplares, devoluciones, reservas, prestamos, usuarios, dashboard


# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(ejemplares.router, prefix=settings.API_V1_STR, tags=["Ejemplares"])
app.include_router(devoluciones.router, prefix=settings.API_V1_STR)
app.include_router(reservas.router, prefix=settings.API_V1_STR)
app.include_router(prestamos.router, prefix=settings.API_V1_STR)
app.include_router(usuarios.router, prefix=settings.API_V1_STR, tags=["Usuarios"])
app.include_router(dashboard.router, prefix=settings.API_V1_STR, tags=["Dashboard"])


#Routes ROL 2
app.include_router(documentos.router, prefix=f"{settings.API_V1_STR}/documentos", tags=["Documentos"])
app.include_router(catalogo.router, prefix=f"{settings.API_V1_STR}/catalogo", tags=["Catálogo"])
app.include_router(catalogo.router_categorias, prefix=f"{settings.API_V1_STR}/categorias", tags=["Categorías"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "API Sistema de Autenticación", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
