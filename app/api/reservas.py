from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from app.database import get_db
from app.models.reserva import Reserva
from app.models.usuario import Usuario
from app.models.documento import Documento
from app.schemas.reserva_schema import (
    ReservaCreate, 
    ReservaResponse, 
    ReservaCancelar,
    ReservaConDocumento
)
from app.utils.auth import get_current_user, require_role

router = APIRouter(prefix="/reservas", tags=["Reservas"])

# ============================================
# DÍA 3: SISTEMA DE RESERVAS
# ============================================

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_reserva(
    reserva_data: ReservaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear una nueva reserva de documento.
    La fecha de reserva debe ser al menos para mañana.
    """
    # Verificar que el documento existe
    documento = db.query(Documento).filter(
        Documento.id == reserva_data.documento_id
    ).first()
    
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con id {reserva_data.documento_id} no encontrado"
        )
    
    # Verificar que el usuario no tenga ya una reserva activa del mismo documento
    reserva_existente = db.query(Reserva).filter(
        Reserva.usuario_id == current_user.id,
        Reserva.documento_id == reserva_data.documento_id,
        Reserva.estado.in_(["pendiente", "activa"])
    ).first()
    
    if reserva_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tienes una reserva activa de este documento"
        )
    
    # TODO: Verificar disponibilidad estimada para esa fecha (consulta ROL 3)
    # Por ahora asumimos que está disponible
    
    # Crear reserva
    nueva_reserva = Reserva(
        usuario_id=current_user.id,
        documento_id=reserva_data.documento_id,
        fecha_reserva=reserva_data.fecha_reserva,
        estado="pendiente"
    )
    
    db.add(nueva_reserva)
    db.commit()
    db.refresh(nueva_reserva)
    
    return {
        "success": True,
        "message": "Reserva creada exitosamente",
        "data": {
            "id": nueva_reserva.id,
            "documento_id": nueva_reserva.documento_id,
            "documento_titulo": documento.titulo,
            "fecha_reserva": nueva_reserva.fecha_reserva,
            "estado": nueva_reserva.estado,
            "fecha_creacion": nueva_reserva.fecha_creacion
        }
    }

@router.get("/usuario/{usuario_id}", response_model=List[ReservaResponse])
async def ver_reservas_usuario(
    usuario_id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente, activa, cancelada, completada"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ver todas las reservas de un usuario.
    Un usuario solo puede ver sus propias reservas, admin puede ver todas.
    """
    # Verificar permisos
    if current_user.id != usuario_id and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estas reservas"
        )
    
    query = db.query(Reserva).filter(Reserva.usuario_id == usuario_id)
    
    if estado:
        query = query.filter(Reserva.estado == estado)
    
    reservas = query.order_by(Reserva.fecha_reserva.desc()).all()
    
    return reservas

@router.get("/mis-reservas", response_model=List[dict])
async def ver_mis_reservas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ver las reservas del usuario actual con información del documento.
    """
    query = db.query(Reserva).filter(Reserva.usuario_id == current_user.id)
    
    if estado:
        query = query.filter(Reserva.estado == estado)
    
    reservas = query.order_by(Reserva.fecha_reserva.desc()).all()
    
    # Enriquecer con datos del documento
    resultado = []
    for reserva in reservas:
        documento = db.query(Documento).filter(Documento.id == reserva.documento_id).first()
        
        resultado.append({
            "id": reserva.id,
            "documento_id": reserva.documento_id,
            "documento_titulo": documento.titulo if documento else "N/A",
            "documento_autor": documento.autor if documento else "N/A",
            "fecha_reserva": reserva.fecha_reserva,
            "estado": reserva.estado,
            "fecha_creacion": reserva.fecha_creacion,
            "motivo_cancelacion": reserva.motivo_cancelacion
        })
    
    return resultado

@router.delete("/{reserva_id}", response_model=dict)
async def cancelar_reserva(
    reserva_id: int,
    cancelacion: ReservaCancelar = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cancelar una reserva.
    Solo el usuario dueño o admin pueden cancelar.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Verificar permisos
    if reserva.usuario_id != current_user.id and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta reserva"
        )
    
    # Verificar que se puede cancelar
    if not reserva.puede_cancelar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar una reserva en estado '{reserva.estado}'"
        )
    
    # Cancelar
    reserva.estado = "cancelada"
    if cancelacion and cancelacion.motivo:
        reserva.motivo_cancelacion = cancelacion.motivo
    else:
        reserva.motivo_cancelacion = "Cancelada por el usuario"
    
    reserva.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Reserva cancelada exitosamente",
        "data": {
            "id": reserva.id,
            "estado": reserva.estado,
            "motivo_cancelacion": reserva.motivo_cancelacion
        }
    }

@router.get("/", response_model=List[dict])
async def listar_todas_reservas(
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Listar todas las reservas del sistema (solo admin/bibliotecario).
    Con filtros de estado y fecha.
    """
    query = db.query(Reserva)
    
    if estado:
        query = query.filter(Reserva.estado == estado)
    
    if fecha_desde:
        query = query.filter(Reserva.fecha_reserva >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(Reserva.fecha_reserva <= fecha_hasta)
    
    reservas = query.order_by(Reserva.fecha_reserva.asc()).offset(skip).limit(limit).all()
    
    # Enriquecer con datos
    resultado = []
    for reserva in reservas:
        usuario = db.query(Usuario).filter(Usuario.id == reserva.usuario_id).first()
        documento = db.query(Documento).filter(Documento.id == reserva.documento_id).first()
        
        resultado.append({
            "id": reserva.id,
            "usuario_rut": usuario.rut if usuario else "N/A",
            "usuario_nombre": f"{usuario.nombres} {usuario.apellidos}" if usuario else "N/A",
            "documento_id": reserva.documento_id,
            "documento_titulo": documento.titulo if documento else "N/A",
            "fecha_reserva": reserva.fecha_reserva,
            "estado": reserva.estado,
            "fecha_creacion": reserva.fecha_creacion
        })
    
    return resultado

@router.patch("/{reserva_id}/completar", response_model=dict)
async def marcar_reserva_completada(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Marcar una reserva como completada.
    Se usa cuando el usuario retira el documento reservado.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reserva.estado != "activa":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden completar reservas activas (estado actual: {reserva.estado})"
        )
    
    reserva.estado = "completada"
    reserva.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Reserva marcada como completada",
        "data": {
            "id": reserva.id,
            "estado": reserva.estado
        }
    }

@router.patch("/{reserva_id}/activar", response_model=dict)
async def activar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Activar una reserva pendiente.
    Se usa cuando llega la fecha de la reserva.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reserva.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden activar reservas pendientes (estado actual: {reserva.estado})"
        )
    
    reserva.estado = "activa"
    reserva.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Reserva activada exitosamente",
        "data": {
            "id": reserva.id,
            "estado": reserva.estado
        }
    }

@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas_reservas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Obtener estadísticas generales de reservas.
    """
    total = db.query(Reserva).count()
    pendientes = db.query(Reserva).filter(Reserva.estado == "pendiente").count()
    activas = db.query(Reserva).filter(Reserva.estado == "activa").count()
    completadas = db.query(Reserva).filter(Reserva.estado == "completada").count()
    canceladas = db.query(Reserva).filter(Reserva.estado == "cancelada").count()
    
    return {
        "total_reservas": total,
        "pendientes": pendientes,
        "activas": activas,
        "completadas": completadas,
        "canceladas": canceladas,
        "tasa_cancelacion": round((canceladas / total * 100) if total > 0 else 0, 2)
    }
