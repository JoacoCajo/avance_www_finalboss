from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.ejemplar import Ejemplar
from app.models.historial_ejemplar import HistorialEjemplar
from app.models.usuario import Usuario
from app.schemas.ejemplar_schema import (
    EjemplarCreate, 
    EjemplarResponse, 
    EjemplarEstadoUpdate,
    DisponibilidadResponse,
    HistorialEjemplarResponse
)
from app.utils.auth import get_current_user, require_role
import random
import string
from sqlalchemy import func
from datetime import timedelta, datetime
from pydantic import BaseModel


router = APIRouter(prefix="/ejemplares", tags=["Ejemplares"])

ESTADOS_VALIDOS = ["disponible", "prestado", "en_sala", "devuelto", "mantenimiento", "perdido"]

# ============================================
# CLASES INTERNAS
# ============================================
class ValidarPrestamoRequest(BaseModel):
    ejemplares_ids: List[int]


# ============================================
# FUNCIONES AUXILIARES INTERNAS
# ============================================

def generar_codigo_ejemplar(documento_id: int, db: Session) -> str:
    """
    Generar código único para ejemplar.
    Formato: DOC-{documento_id}-{número correlativo}
    Ejemplo: DOC-1-001, DOC-1-002, etc.
    """
    # Contar cuántos ejemplares tiene este documento
    count = db.query(Ejemplar).filter(Ejemplar.documento_id == documento_id).count()
    nuevo_numero = count + 1
    
    # Generar código con formato
    codigo_base = f"DOC-{documento_id}-{nuevo_numero:03d}"
    
    # Verificar que no exista (por si acaso)
    while db.query(Ejemplar).filter(Ejemplar.codigo == codigo_base).first():
        nuevo_numero += 1
        codigo_base = f"DOC-{documento_id}-{nuevo_numero:03d}"
    
    return codigo_base

# ============================================
# ENDPOINT 7: Estadísticas de ejemplares (NUEVO)
# ============================================
@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Obtener estadísticas generales de ejemplares.
    Útil para dashboard de bibliotecario.
    """
    total = db.query(Ejemplar).count()
    disponibles = db.query(Ejemplar).filter(Ejemplar.estado == "disponible").count()
    prestados = db.query(Ejemplar).filter(Ejemplar.estado == "prestado").count()
    en_sala = db.query(Ejemplar).filter(Ejemplar.estado == "en_sala").count()
    mantenimiento = db.query(Ejemplar).filter(Ejemplar.estado == "mantenimiento").count()
    perdidos = db.query(Ejemplar).filter(Ejemplar.estado == "perdido").count()
    
    return {
        "total_ejemplares": total,
        "disponibles": disponibles,
        "prestados": prestados,
        "en_sala": en_sala,
        "en_mantenimiento": mantenimiento,
        "perdidos": perdidos,
        "porcentaje_disponibilidad": round((disponibles / total * 100) if total > 0 else 0, 2)
    }

# ============================================
# ENDPOINT 16: Ejemplares con problemas (MEDIANA)
# ============================================
@router.get("/reportes/con-problemas", response_model=dict)
async def obtener_ejemplares_con_problemas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Reporte de ejemplares que requieren atención:
    - Perdidos
    - En mantenimiento
    - Historial de cambios frecuentes (posible problema)
    
    Útil para gestión preventiva de la colección.
    """
    perdidos = db.query(Ejemplar).filter(Ejemplar.estado == "perdido").all()
    en_mantenimiento = db.query(Ejemplar).filter(Ejemplar.estado == "mantenimiento").all()
    
    # Ejemplares con más de 5 cambios de estado (posible problema)
    from sqlalchemy import func
    problematicos = db.query(
        Ejemplar,
        func.count(HistorialEjemplar.id).label("cambios")
    ).join(
        HistorialEjemplar, Ejemplar.id == HistorialEjemplar.ejemplar_id
    ).group_by(Ejemplar.id).having(
        func.count(HistorialEjemplar.id) > 5
    ).all()
    
    return {
        "perdidos": {
            "total": len(perdidos),
            "ejemplares": [
                {
                    "id": e.id,
                    "codigo": e.codigo,
                    "documento_id": e.documento_id,
                    "ubicacion": e.ubicacion
                }
                for e in perdidos
            ]
        },
        "en_mantenimiento": {
            "total": len(en_mantenimiento),
            "ejemplares": [
                {
                    "id": e.id,
                    "codigo": e.codigo,
                    "documento_id": e.documento_id,
                    "ubicacion": e.ubicacion
                }
                for e in en_mantenimiento
            ]
        },
        "problematicos": {
            "total": len(problematicos),
            "ejemplares": [
                {
                    "id": e.id,
                    "codigo": e.codigo,
                    "documento_id": e.documento_id,
                    "cambios_estado": cambios,
                    "estado_actual": e.estado
                }
                for e, cambios in problematicos
            ]
        }
    }


# ============================================
# ENDPOINT 17: Reporte de uso por ubicación (MEDIANA)
# ============================================
@router.get("/reportes/por-ubicacion", response_model=dict)
async def obtener_reporte_ubicaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Reporte de ejemplares agrupados por ubicación.
    Útil para organización física de la biblioteca.
    """
    from sqlalchemy import func
    
    ubicaciones = db.query(
        Ejemplar.ubicacion,
        func.count(Ejemplar.id).label("total"),
        func.sum(func.case((Ejemplar.estado == "disponible", 1), else_=0)).label("disponibles"),
        func.sum(func.case((Ejemplar.estado == "prestado", 1), else_=0)).label("prestados")
    ).group_by(Ejemplar.ubicacion).all()
    
    return {
        "total_ubicaciones": len(ubicaciones),
        "ubicaciones": [
            {
                "ubicacion": u or "Sin ubicación",
                "total_ejemplares": total,
                "disponibles": disponibles or 0,
                "prestados": prestados or 0,
                "tasa_ocupacion": round((prestados or 0) / total * 100, 2) if total > 0 else 0
            }
            for u, total, disponibles, prestados in ubicaciones
        ]
    }

# ============================================
# ENDPOINT 18: Sistema de alertas (MEDIANA)
# ============================================
@router.get("/alertas", response_model=dict)
async def obtener_alertas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Sistema de alertas para el bibliotecario.
    Muestra situaciones que requieren atención inmediata.
    """
    alertas = []
    
    # Alerta 1: Ejemplares perdidos
    perdidos = db.query(Ejemplar).filter(Ejemplar.estado == "perdido").count()
    if perdidos > 0:
        alertas.append({
            "tipo": "perdidos",
            "severidad": "alta",
            "mensaje": f"{perdidos} ejemplar(es) marcado(s) como perdido(s)",
            "accion": "Revisar recuperación o dar de baja"
        })
    
    # Alerta 2: Ejemplares en mantenimiento hace mucho tiempo
    # (más de 30 días - simplificado: más de 30 registros en historial)
    
    
    hace_30_dias = datetime.utcnow() - timedelta(days=30)
    mantenimiento_largo = db.query(Ejemplar).filter(
        Ejemplar.estado == "mantenimiento"
    ).join(
        HistorialEjemplar, Ejemplar.id == HistorialEjemplar.ejemplar_id
    ).filter(
        HistorialEjemplar.estado_nuevo == "mantenimiento",
        HistorialEjemplar.created_at < hace_30_dias
    ).count()
    
    if mantenimiento_largo > 0:
        alertas.append({
            "tipo": "mantenimiento_prolongado",
            "severidad": "media",
            "mensaje": f"{mantenimiento_largo} ejemplar(es) en mantenimiento por más de 30 días",
            "accion": "Revisar estado de reparación"
        })
    
    # Alerta 3: Baja disponibilidad en documentos populares
    # (menos del 20% disponible y más de 5 ejemplares totales)
    documentos_baja_disponibilidad = []
    
    docs_query = db.query(Ejemplar.documento_id).group_by(Ejemplar.documento_id).all()
    
    for (doc_id,) in docs_query:
        total = db.query(Ejemplar).filter(Ejemplar.documento_id == doc_id).count()
        disponibles = db.query(Ejemplar).filter(
            Ejemplar.documento_id == doc_id,
            Ejemplar.estado == "disponible"
        ).count()
        
        if total >= 5 and disponibles / total < 0.2:
            documentos_baja_disponibilidad.append({
                "documento_id": doc_id,
                "total": total,
                "disponibles": disponibles
            })
    
    if documentos_baja_disponibilidad:
        alertas.append({
            "tipo": "baja_disponibilidad",
            "severidad": "media",
            "mensaje": f"{len(documentos_baja_disponibilidad)} documento(s) con menos del 20% de disponibilidad",
            "accion": "Considerar adquirir más ejemplares",
            "documentos": documentos_baja_disponibilidad
        })
    
    # Alerta 4: Sin ubicación asignada
    sin_ubicacion = db.query(Ejemplar).filter(
        (Ejemplar.ubicacion == None) | (Ejemplar.ubicacion == "")
    ).count()
    
    if sin_ubicacion > 0:
        alertas.append({
            "tipo": "sin_ubicacion",
            "severidad": "baja",
            "mensaje": f"{sin_ubicacion} ejemplar(es) sin ubicación asignada",
            "accion": "Asignar ubicación en estantería"
        })
    
    return {
        "total_alertas": len(alertas),
        "alertas": alertas,
        "timestamp": datetime.utcnow()
    }


# ============================================
# ENDPOINT 6: Listar ejemplares disponibles
# ============================================
@router.get("/disponibles", response_model=List[EjemplarResponse])
def listar_disponibles(documento_id: int = None, db: Session = Depends(get_db)):
    """
    Listar todos los ejemplares disponibles.
    Opcionalmente filtrar por documento_id.
    """
    query = db.query(Ejemplar).filter(Ejemplar.estado == "disponible")
    
    if documento_id:
        query = query.filter(Ejemplar.documento_id == documento_id)
    
    ejemplares = query.all()
    return ejemplares

# PARTE 2

# ============================================
# ENDPOINT 3: Ver disponibilidad de un documento
# ============================================
@router.get("/documento/{documento_id}/disponibilidad", response_model=DisponibilidadResponse)
def obtener_disponibilidad(documento_id: int, db: Session = Depends(get_db)):
    """
    Obtener conteo de disponibilidad de un documento.
    
    FUNCIÓN CLAVE para ROL 2 (búsqueda) y ROL 4 (préstamos).
    """
    ejemplares = db.query(Ejemplar).filter(
        Ejemplar.documento_id == documento_id
    ).all()
    
    if not ejemplares:
        return DisponibilidadResponse(
            disponibles=0,
            prestados=0,
            en_sala=0,
            mantenimiento=0,
            total=0,
            puede_solicitar=False
        )
    
    # Contar por estado
    disponibles = sum(1 for e in ejemplares if e.estado == "disponible")
    prestados = sum(1 for e in ejemplares if e.estado == "prestado")
    en_sala = sum(1 for e in ejemplares if e.estado == "en_sala")
    mantenimiento = sum(1 for e in ejemplares if e.estado == "mantenimiento")
    
    return DisponibilidadResponse(
        disponibles=disponibles,
        prestados=prestados,
        en_sala=en_sala,
        mantenimiento=mantenimiento,
        total=len(ejemplares),
        puede_solicitar=disponibles > 0
    )


# ============================================
# ENDPOINT 11: Obtener ejemplares disponibles de un documento (NUEVO)
# ============================================
@router.get("/documento/{documento_id}/disponibles", response_model=List[EjemplarResponse])
async def obtener_ejemplares_disponibles_documento(
    documento_id: int,
    cantidad: int = None,
    db: Session = Depends(get_db)
):
    """
    Obtener ejemplares disponibles de un documento específico.
    Si se especifica 'cantidad', retorna solo esa cantidad.
    
    Útil para ROL 4: cuando el usuario pide "1 copia de Harry Potter",
    este endpoint retorna qué ejemplares específicos están disponibles.
    
    Ejemplos:
    - GET /documento/1/disponibles → todos los disponibles
    - GET /documento/1/disponibles?cantidad=2 → máximo 2
    """
    query = db.query(Ejemplar).filter(
        Ejemplar.documento_id == documento_id,
        Ejemplar.estado == "disponible"
    )
    
    if cantidad:
        query = query.limit(cantidad)
    
    ejemplares = query.all()
    
    if not ejemplares:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay ejemplares disponibles del documento {documento_id}"
        )
    

# ============================================
# ENDPOINT 2: Listar ejemplares de un documento
# ============================================
@router.get("/documento/{documento_id}", response_model=List[EjemplarResponse])
def listar_ejemplares_documento(documento_id: int, db: Session = Depends(get_db)):
    """
    Obtener todos los ejemplares de un documento específico.
    Usado por ROL 2 para mostrar disponibilidad en la búsqueda.
    """
    ejemplares = db.query(Ejemplar).filter(
        Ejemplar.documento_id == documento_id
    ).all()
    
    return ejemplares


# ============================================
# ENDPOINT 5: Buscar ejemplar por código
# ============================================
@router.get("/codigo/{codigo}", response_model=EjemplarResponse)
def buscar_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """
    Buscar un ejemplar específico por su código único.
    Usado al momento de devoluciones (ROL 4).
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.codigo == codigo).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe ejemplar con código {codigo}"
        )
    
    return ejemplar

# ============================================
# ENDPOINT 9: Buscar ejemplares por ubicación (NUEVO)
# ============================================
@router.get("/ubicacion/{ubicacion}", response_model=List[EjemplarResponse])
async def buscar_por_ubicacion(
    ubicacion: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Buscar todos los ejemplares en una ubicación específica.
    Útil para inventario o reorganización de estanterías.
    Ejemplo: /ubicacion/A3-E2
    """
    ejemplares = db.query(Ejemplar).filter(
        Ejemplar.ubicacion.ilike(f"%{ubicacion}%")
    ).all()
    
    return ejemplares


# Parte 3


# ============================================
# ENDPOINT 1: Crear ejemplar (REQUIERE AUTH)
# ============================================
@router.post("/", response_model=EjemplarResponse, status_code=status.HTTP_201_CREATED)
async def crear_ejemplar(
    ejemplar: EjemplarCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"])),
    auto_codigo: bool = Query(False, description="Generar código automáticamente")
):
    """
    Crear un nuevo ejemplar de un documento.
    Solo bibliotecarios/admin pueden crear ejemplares.
    REQUIERE AUTENTICACIÓN.
    
    Si auto_codigo=true, genera el código automáticamente.
    """
    codigo_final = ejemplar.codigo
    
    # Si se solicita auto-código, generarlo
    if auto_codigo:
        codigo_final = generar_codigo_ejemplar(ejemplar.documento_id, db)
    else:
        # Verificar que el código no exista
        existe = db.query(Ejemplar).filter(Ejemplar.codigo == codigo_final).first()
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un ejemplar con el código {codigo_final}"
            )
    
    # TODO: Verificar que documento_id exista (cuando ROL 2 esté listo)
    
    nuevo_ejemplar = Ejemplar(
        documento_id=ejemplar.documento_id,
        codigo=codigo_final,
        ubicacion=ejemplar.ubicacion,
        estado="disponible"
    )
    
    db.add(nuevo_ejemplar)
    db.commit()
    db.refresh(nuevo_ejemplar)
    
    return nuevo_ejemplar

# ============================================
# ENDPOINT 10: Validar disponibilidad para préstamo (NUEVO)
# ============================================
@router.post("/validar-prestamo", response_model=dict)
async def validar_disponibilidad_prestamo(
    request: ValidarPrestamoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Validar que múltiples ejemplares estén disponibles para préstamo.
    Usado por ROL 4 antes de crear un préstamo.
    
    Body: {"ejemplares_ids": [1, 2, 3]}
    """
    resultados = []
    todos_disponibles = True
    
    ejemplares_ids = request.ejemplares_ids

    for ejemplar_id in ejemplares_ids:
        ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
        
        if not ejemplar:
            resultados.append({
                "ejemplar_id": ejemplar_id,
                "disponible": False,
                "razon": "Ejemplar no existe"
            })
            todos_disponibles = False
        elif ejemplar.estado != "disponible":
            resultados.append({
                "ejemplar_id": ejemplar_id,
                "codigo": ejemplar.codigo,
                "disponible": False,
                "estado_actual": ejemplar.estado,
                "razon": f"Ejemplar no disponible (estado: {ejemplar.estado})"
            })
            todos_disponibles = False
        else:
            resultados.append({
                "ejemplar_id": ejemplar_id,
                "codigo": ejemplar.codigo,
                "disponible": True,
                "ubicacion": ejemplar.ubicacion
            })
    
    return {
        "todos_disponibles": todos_disponibles,
        "total_ejemplares": len(ejemplares_ids),
        "disponibles": sum(1 for r in resultados if r.get("disponible")),
        "detalles": resultados
    }


# Parte 4

# ============================================
# ENDPOINT 15: Ver historial de cambios de un ejemplar (MEDIANA)
# ============================================
@router.get("/{ejemplar_id}/historial", response_model=List[HistorialEjemplarResponse])
async def obtener_historial_ejemplar(
    ejemplar_id: int,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Obtener el historial completo de cambios de estado de un ejemplar.
    Útil para auditoría y trazabilidad.
    
    Muestra quién cambió el estado, cuándo y por qué.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejemplar con id {ejemplar_id} no encontrado"
        )
    
    historial = db.query(HistorialEjemplar).filter(
        HistorialEjemplar.ejemplar_id == ejemplar_id
    ).order_by(HistorialEjemplar.created_at.desc()).limit(limit).all()
    
    return historial

# ============================================
# ENDPOINT 4: Actualizar estado de ejemplar (REQUIERE AUTH)
# ============================================
@router.patch("/{ejemplar_id}/estado", response_model=EjemplarResponse)
async def actualizar_estado_ejemplar(
    ejemplar_id: int, 
    estado_update: EjemplarEstadoUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"])),
    motivo: Optional[str] = Query(None, description="Motivo del cambio de estado")
):
    """
    Cambiar el estado de un ejemplar.
    Usado por ROL 4 cuando se registra un préstamo o devolución.
    REQUIERE AUTENTICACIÓN: solo bibliotecario o admin.
    
    Ahora registra el cambio en el historial.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejemplar con id {ejemplar_id} no encontrado"
        )
    
    # Validar estado
    nuevo_estado = estado_update.estado.lower()
    if nuevo_estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Estados válidos: {', '.join(ESTADOS_VALIDOS)}"
        )
    
    # Guardar estado anterior para el historial
    estado_anterior = ejemplar.estado
    
    # Actualizar estado
    ejemplar.estado = nuevo_estado
    
    # Registrar en historial
    historial = HistorialEjemplar(
        ejemplar_id=ejemplar_id,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        usuario_id=current_user.id,
        motivo=motivo
    )
    db.add(historial)
    
    db.commit()
    db.refresh(ejemplar)
    
    return ejemplar

# ============================================
# ENDPOINT 8: Actualizar ubicación de ejemplar (NUEVO)
# ============================================
@router.patch("/{ejemplar_id}/ubicacion", response_model=EjemplarResponse)
async def actualizar_ubicacion(
    ejemplar_id: int,
    nueva_ubicacion: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Actualizar la ubicación física de un ejemplar.
    Útil cuando se reorganizan las estanterías.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejemplar con id {ejemplar_id} no encontrado"
        )
    
    ejemplar.ubicacion = nueva_ubicacion
    db.commit()
    db.refresh(ejemplar)
    
    return ejemplar

# ============================================
# ENDPOINT 12: Marcar ejemplar como perdido (FÁCIL)
# ============================================
@router.patch("/{ejemplar_id}/marcar-perdido", response_model=EjemplarResponse)
async def marcar_como_perdido(
    ejemplar_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Marcar un ejemplar como perdido.
    Útil cuando un ejemplar no se devuelve y se da por perdido.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejemplar con id {ejemplar_id} no encontrado"
        )
    
    ejemplar.estado = "perdido"
    db.commit()
    db.refresh(ejemplar)
    
    return ejemplar

# ============================================
# ENDPOINT 13: Recuperar ejemplar perdido (FÁCIL)
# ============================================
@router.patch("/{ejemplar_id}/recuperar", response_model=EjemplarResponse)
async def recuperar_ejemplar(
    ejemplar_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "bibliotecario"]))
):
    """
    Recuperar un ejemplar que estaba perdido y marcarlo como disponible.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejemplar con id {ejemplar_id} no encontrado"
        )
    
    if ejemplar.estado != "perdido":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ejemplar no está marcado como perdido (estado actual: {ejemplar.estado})"
        )
    
    ejemplar.estado = "disponible"
    db.commit()
    db.refresh(ejemplar)
    
    return ejemplar

# ============================================
# ENDPOINT 14: Listar ejemplares con filtros múltiples (FÁCIL)
# ============================================
@router.get("/", response_model=List[EjemplarResponse])
async def listar_ejemplares_con_filtros(
    documento_id: Optional[int] = Query(None, description="Filtrar por documento"),
    estados: Optional[str] = Query(None, description="Estados separados por coma (ej: disponible,prestado)"),
    ubicacion: Optional[str] = Query(None, description="Filtrar por ubicación (búsqueda parcial)"),
    limit: int = Query(100, le=500, description="Límite de resultados"),
    offset: int = Query(0, description="Offset para paginación"),
    db: Session = Depends(get_db)
):
    """
    Listar ejemplares con múltiples filtros opcionales.
    
    Ejemplos:
    - GET /ejemplares?estados=disponible,en_sala
    - GET /ejemplares?documento_id=1&estados=prestado
    - GET /ejemplares?ubicacion=A3
    - GET /ejemplares?limit=10&offset=0
    """
    query = db.query(Ejemplar)
    
    # Filtro por documento
    if documento_id:
        query = query.filter(Ejemplar.documento_id == documento_id)
    
    # Filtro por estados (múltiples)
    if estados:
        lista_estados = [e.strip() for e in estados.split(",")]
        query = query.filter(Ejemplar.estado.in_(lista_estados))
    
    # Filtro por ubicación (búsqueda parcial)
    if ubicacion:
        query = query.filter(Ejemplar.ubicacion.ilike(f"%{ubicacion}%"))
    
    # Paginación
    query = query.offset(offset).limit(limit)
    
    ejemplares = query.all()
    return ejemplares

# ============================================
# FUNCIONES AUXILIARES para otros roles
# ============================================

def marcar_prestado(ejemplar_id: int, db: Session) -> bool:
    """
    Función para ROL 4: Marcar ejemplar como prestado.
    Retorna True si fue exitoso, False si no estaba disponible.
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        return False
    
    if ejemplar.estado != "disponible":
        return False
    
    ejemplar.estado = "prestado"
    db.commit()
    return True


def marcar_devuelto(ejemplar_id: int, db: Session) -> bool:
    """
    Función para ROL 4: Marcar ejemplar como devuelto.
    Después de 30 min debería cambiar a disponible (simplificado: directo a disponible).
    """
    ejemplar = db.query(Ejemplar).filter(Ejemplar.id == ejemplar_id).first()
    
    if not ejemplar:
        return False
    
    if ejemplar.estado not in ["prestado", "en_sala"]:
        return False
    
    # Simplificado: cambiar directo a disponible
    ejemplar.estado = "disponible"
    db.commit()
    return True


def get_disponibilidad_rapida(documento_id: int, db: Session) -> dict:
    """
    Función rápida para ROL 2: solo retorna si hay disponibles y cuántos.
    """
    disponibles = db.query(Ejemplar).filter(
        Ejemplar.documento_id == documento_id,
        Ejemplar.estado == "disponible"
    ).count()
    
    return {
        "disponibles": disponibles,
        "puede_solicitar": disponibles > 0
    }


