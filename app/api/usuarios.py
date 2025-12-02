from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models.usuario import Usuario
from app.models.token_validacion import TokenValidacion
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.utils.auth import get_current_user, require_role
from app.utils.validations import validar_rut, formatear_rut
from app.services.email_service import email_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# ============================================
# DÍA 1: CRUD USUARIOS
# ============================================

@router.post("/registrar", response_model=dict, status_code=status.HTTP_201_CREATED)
async def registrar_usuario_completo(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar usuario con todos los campos.
    Crea el usuario en estado pendiente y envía email de validación.
    """
    # Validar RUT
    if not validar_rut(usuario_data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    rut_formateado = formatear_rut(usuario_data.rut)
    
    # Verificar RUT único
    if db.query(Usuario).filter(Usuario.rut == rut_formateado).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El RUT ya está registrado"
        )
    
    # Verificar email único
    if db.query(Usuario).filter(Usuario.email == usuario_data.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    nuevo_usuario = Usuario(
        rut=rut_formateado,
        nombres=usuario_data.nombres,
        apellidos=usuario_data.apellidos,
        email=usuario_data.email.lower(),
        rol=usuario_data.rol or "usuario",
        activo=False  # Pendiente de activación
    )
    nuevo_usuario.set_password(usuario_data.password)
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    # Generar token de validación
    token = TokenValidacion.crear_token(nuevo_usuario.id)
    db.add(token)
    db.commit()
    
    # Enviar email de validación
    email_enviado = email_service.send_validation_email(
        to=nuevo_usuario.email,
        nombre=nuevo_usuario.nombres,
        token=token.token
    )
    
    return {
        "success": True,
        "message": "Usuario registrado exitosamente. Revisa tu correo para activar la cuenta.",
        "email_enviado": email_enviado,
        "data": {
            "id": nuevo_usuario.id,
            "rut": nuevo_usuario.rut,
            "nombres": nuevo_usuario.nombres,
            "apellidos": nuevo_usuario.apellidos,
            "email": nuevo_usuario.email,
            "rol": nuevo_usuario.rol,
            "activo": nuevo_usuario.activo
        }
    }

@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    rol: Optional[str] = Query(None, description="Filtrar por rol"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, le=500, description="Límite de resultados"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """
    Listar todos los usuarios (solo admin).
    Permite filtrar por estado y rol.
    """
    query = db.query(Usuario)
    
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    if rol:
        query = query.filter(Usuario.rol == rol)
    
    usuarios = query.offset(skip).limit(limit).all()
    
    # Agregar campo sancionado a la respuesta
    resultado = []
    for u in usuarios:
        usuario_dict = {
            "id": u.id,
            "rut": u.rut,
            "nombres": u.nombres,
            "apellidos": u.apellidos,
            "email": u.email,
            "rol": u.rol,
            "activo": u.activo,
            "foto_url": u.foto_url,
            "sancionado": u.esta_sancionado(),
            "fecha_sancion_hasta": u.fecha_sancion_hasta,
            "created_at": u.created_at
        }
        resultado.append(UsuarioResponse(**usuario_dict))
    
    return resultado

@router.get("/{usuario_id}", response_model=dict)
async def ver_detalle_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ver detalle completo de un usuario.
    El usuario puede ver su propia info, admin puede ver cualquiera.
    Incluye préstamos activos y reservas.
    """
    # Verificar permisos
    if current_user.id != usuario_id and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario"
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # TODO: Consultar préstamos activos (ROL 4)
    # prestamos_activos = obtener_prestamos_activos(usuario_id, db)
    
    # Consultar reservas activas
    from app.models.reserva import Reserva
    reservas_activas = db.query(Reserva).filter(
        Reserva.usuario_id == usuario_id,
        Reserva.estado.in_(["pendiente", "activa"])
    ).all()
    
    return {
        "success": True,
        "data": {
            "id": usuario.id,
            "rut": usuario.rut,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "email": usuario.email,
            "rol": usuario.rol,
            "activo": usuario.activo,
            "foto_url": usuario.foto_url,
            "sancionado": usuario.esta_sancionado(),
            "fecha_sancion_hasta": usuario.fecha_sancion_hasta,
            "created_at": usuario.created_at,
            "estadisticas": {
                "prestamos_activos": 0,  # TODO: integrar con ROL 4
                "reservas_activas": len(reservas_activas)
            }
        }
    }

@router.put("/{usuario_id}", response_model=dict)
async def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar datos de usuario.
    - Admin puede actualizar cualquier campo
    - Usuario solo puede actualizar: dirección, teléfono, email, foto
    """
    # Verificar permisos
    if current_user.id != usuario_id and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario"
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos permitidos
    update_data = usuario_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(usuario, field):
            setattr(usuario, field, value)
    
    db.commit()
    db.refresh(usuario)
    
    return {
        "success": True,
        "message": "Usuario actualizado exitosamente",
        "data": {
            "id": usuario.id,
            "rut": usuario.rut,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "email": usuario.email,
            "rol": usuario.rol,
            "activo": usuario.activo
        }
    }

@router.patch("/{usuario_id}/estado", response_model=dict)
async def cambiar_estado_usuario(
    usuario_id: int,
    activo: bool,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """
    Activar/Desactivar usuario (solo admin).
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = activo
    db.commit()
    
    return {
        "success": True,
        "message": f"Usuario {'activado' if activo else 'desactivado'} exitosamente",
        "data": {
            "id": usuario.id,
            "activo": usuario.activo
        }
    }

# ============================================
# DÍA 2: ACTIVACIÓN DE CUENTAS
# ============================================

@router.get("/activar/{token}", response_model=dict)
async def activar_cuenta(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Activar cuenta de usuario mediante token enviado por email.
    El token tiene una validez de 24 horas.
    """
    # Buscar token
    token_obj = db.query(TokenValidacion).filter(
        TokenValidacion.token == token
    ).first()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token inválido o no encontrado"
        )
    
    # Verificar si ya fue usado
    if token_obj.usado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token ya fue utilizado"
        )
    
    # Verificar si expiró
    if token_obj.esta_expirado():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token ha expirado. Solicita un nuevo enlace de activación."
        )
    
    # Activar usuario
    usuario = db.query(Usuario).filter(Usuario.id == token_obj.usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = True
    token_obj.usado = True
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Cuenta activada exitosamente. Bienvenido, {usuario.nombres}!",
        "data": {
            "usuario_id": usuario.id,
            "nombres": usuario.nombres,
            "email": usuario.email,
            "activo": usuario.activo
        }
    }

@router.post("/{usuario_id}/reenviar-activacion", response_model=dict)
async def reenviar_email_activacion(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Reenviar email de activación si el usuario no lo recibió o expiró.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta ya está activa"
        )
    
    # Invalidar tokens anteriores
    tokens_anteriores = db.query(TokenValidacion).filter(
        TokenValidacion.usuario_id == usuario_id,
        TokenValidacion.usado == False
    ).all()
    
    for t in tokens_anteriores:
        t.usado = True
    
    # Generar nuevo token
    nuevo_token = TokenValidacion.crear_token(usuario_id)
    db.add(nuevo_token)
    db.commit()
    
    # Enviar email
    email_enviado = email_service.send_validation_email(
        to=usuario.email,
        nombre=usuario.nombres,
        token=nuevo_token.token
    )
    
    return {
        "success": True,
        "message": "Email de activación reenviado",
        "email_enviado": email_enviado
    }

# ============================================
# FUNCIONES AUXILIARES para otros roles
# ============================================

def obtener_usuario_por_rut(rut: str, db: Session) -> Optional[Usuario]:
    """
    Función auxiliar para ROL 4 (préstamos).
    Buscar usuario por RUT.
    """
    rut_formateado = formatear_rut(rut)
    return db.query(Usuario).filter(Usuario.rut == rut_formateado).first()

def verificar_usuario_puede_prestar(usuario_id: int, db: Session) -> dict:
    """
    Función auxiliar para ROL 4 (préstamos).
    Verificar si un usuario puede solicitar préstamos.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        return {"puede": False, "razones": ["Usuario no encontrado"]}
    
    if not usuario.activo:
        return {"puede": False, "razones": ["Cuenta no activada"]}
    
    if usuario.esta_sancionado():
        return {
            "puede": False, 
            "razones": [f"Usuario sancionado hasta {usuario.fecha_sancion_hasta}"]
        }
    
    # TODO: Verificar préstamos vencidos (integrar con ROL 4)
    # TODO: Verificar límite de préstamos activos (máx 3)
    
    return {"puede": True, "razones": []}