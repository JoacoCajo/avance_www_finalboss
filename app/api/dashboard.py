from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.documento import Documento
from app.models.usuario import Usuario
from app.models.prestamos import Prestamo, EstadoPrestamo

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=dict)
def obtener_estadisticas_dashboard(db: Session = Depends(get_db)):
    """
    Devuelve métricas básicas para el dashboard.
    """
    try:
        total_libros = db.query(Documento).count()
        usuarios_registrados = db.query(Usuario).count()

        # Manejar enum o string en la columna estado
        estado_activo = EstadoPrestamo.activo if hasattr(EstadoPrestamo, "activo") else "activo"
        estado_vencido = EstadoPrestamo.vencido if hasattr(EstadoPrestamo, "vencido") else "vencido"

        prestamos_activos = db.query(Prestamo).filter(Prestamo.estado == estado_activo).count()
        prestamos_atrasados = db.query(Prestamo).filter(Prestamo.estado == estado_vencido).count()

        return {
            "total_libros": total_libros,
            "usuarios_registrados": usuarios_registrados,
            "prestamos_activos": prestamos_activos,
            "prestamos_atrasados": prestamos_atrasados,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
