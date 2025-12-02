from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.usuario import Usuario
from app.utils.auth import get_current_user, require_role
from typing import Optional

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/usuarios", response_model=dict)
async def listar_usuarios(
    activo: Optional[bool] = Query(None),
    rol: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """Listar usuarios con filtros"""
    query = db.query(Usuario)
    
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    if rol:
        query = query.filter(Usuario.rol == rol)
    
    usuarios = query.all()
    
    return {
        "success": True,
        "data": [
            {
                "id": u.id,
                "rut": u.rut,
                "nombres": u.nombres,
                "apellidos": u.apellidos,
                "email": u.email,
                "rol": u.rol,
                "activo": u.activo,
                "sancionado": u.esta_sancionado()
            }
            for u in usuarios
        ]
    }

@router.patch("/usuarios/{usuario_id}/activar", response_model=dict)
async def activar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """Activar usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = True
    db.commit()
    
    return {
        "success": True,
        "message": f"Usuario {usuario.nombres} {usuario.apellidos} activado",
        "data": {"id": usuario.id, "activo": usuario.activo}
    }

@router.patch("/usuarios/{usuario_id}/sancionar", response_model=dict)
async def sancionar_usuario(
    usuario_id: int,
    dias: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """Sancionar usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.fecha_sancion_hasta = datetime.utcnow() + timedelta(days=dias)
    db.commit()
    
    return {
        "success": True,
        "message": f"Usuario sancionado hasta {usuario.fecha_sancion_hasta}",
        "data": {"id": usuario.id, "fecha_sancion_hasta": usuario.fecha_sancion_hasta}
    }
