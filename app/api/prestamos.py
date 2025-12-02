from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.models.prestamos import Prestamo, DetallePrestamo, TipoPrestamo, EstadoPrestamo
from app.models.ejemplar import Ejemplar
from app.models.documento import Documento
from app.models.usuario import Usuario
from app.models.biblioteca import Biblioteca
from app.utils.dates import calcular_fecha_devolucion
from app.utils.validations import formatear_rut
from app.schemas.prestamo import PrestamoCreate, PrestamoResponse, PrestamoStats
from app.database import get_db
from typing import List, Optional

router = APIRouter(prefix="/prestamos", tags=["Prestamos"])

class PrestamoSimpleCreate(BaseModel):
    rut: str
    isbn: str
    tipo_prestamo: str = "domicilio"
    biblioteca_id: Optional[int] = None

@router.post("/registrar-desde-rut-isbn", response_model=dict)
def registrar_prestamo_desde_rut_isbn(
    data: PrestamoSimpleCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un préstamo a partir de RUT e ISBN.
    - Busca usuario por RUT.
    - Busca documento por ISBN (campo edicion).
    - Asigna un ejemplar disponible (o crea uno si no existe).
    - Registra el préstamo y marca el ejemplar como prestado.
    """
    rut_formateado = formatear_rut(data.rut)
    usuario = db.query(Usuario).filter(Usuario.rut == rut_formateado).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado para ese RUT")

    documento = db.query(Documento).filter(Documento.edicion == data.isbn).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado para ese ISBN")

    ejemplar = (
        db.query(Ejemplar)
        .filter(Ejemplar.documento_id == documento.id, Ejemplar.estado == "disponible")
        .first()
    )

    # Si no hay ejemplar, crear uno básico para permitir el préstamo
    if not ejemplar:
        ejemplar = Ejemplar(
            documento_id=documento.id,
            codigo=f"AUTO-{documento.id}-{int(datetime.utcnow().timestamp())}",
            estado="disponible"
        )
        db.add(ejemplar)
        db.flush()

    if ejemplar.estado != "disponible":
        raise HTTPException(status_code=400, detail="No hay ejemplares disponibles para este material")

    # Biblioteca
    biblioteca_id = data.biblioteca_id
    if biblioteca_id is None:
        biblioteca = db.query(Biblioteca).filter(Biblioteca.activo == True).first()
        if not biblioteca:
            biblioteca = Biblioteca(nombre="Biblioteca Principal")
            db.add(biblioteca)
            db.flush()
        biblioteca_id = biblioteca.id

    # Tipo de préstamo (mapear a enum)
    try:
        tipo_enum = TipoPrestamo(data.tipo_prestamo)
    except Exception:
        raise HTTPException(status_code=400, detail="tipo_prestamo inválido")

    ahora = datetime.utcnow()
    prestamo = Prestamo(
        tipo_prestamo=tipo_enum,
        usuario_id=usuario.id,
        biblioteca_id=biblioteca_id,
        fecha_prestamo=ahora,
        hora_prestamo=ahora.time(),
        fecha_devolucion_estimada=ahora + timedelta(days=7),
        estado=EstadoPrestamo.activo
    )
    db.add(prestamo)
    db.flush()

    detalle = DetallePrestamo(
        prestamo_id=prestamo.id,
        ejemplar_id=ejemplar.id
    )
    db.add(detalle)

    ejemplar.estado = "prestado"
    db.commit()
    db.refresh(prestamo)

    return {
        "prestamo": {
            "id": prestamo.id,
            "estado": prestamo.estado.value if hasattr(prestamo.estado, "value") else prestamo.estado,
            "fecha_prestamo": prestamo.fecha_prestamo,
            "fecha_devolucion_estimada": prestamo.fecha_devolucion_estimada,
        },
        "usuario": {
            "id": usuario.id,
            "rut": usuario.rut,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
        },
        "documento": {
            "id": documento.id,
            "titulo": documento.titulo,
            "autor": documento.autor,
            "anio": documento.anio,
            "edicion": documento.edicion,
        },
        "detalle": {
            "ejemplar_id": ejemplar.id,
            "codigo": ejemplar.codigo,
        }
    }

@router.get("/buscar-por-isbn/{isbn}", response_model=dict)
def buscar_prestamo_por_isbn(
    isbn: str,
    db: Session = Depends(get_db)
):
    """
    Busca el préstamo activo o vencido de un ejemplar por ISBN (campo edicion del documento).
    Retorna datos del préstamo, usuario y documento.
    """
    # Buscar documento por ISBN
    documento = db.query(Documento).filter(Documento.edicion == isbn).first()
    if not documento:
        raise HTTPException(status_code=404, detail="No se encontró un documento con ese ISBN")

    # Encontrar el préstamo más reciente que no esté devuelto
    prestamo = (
        db.query(Prestamo)
        .join(DetallePrestamo, Prestamo.id == DetallePrestamo.prestamo_id)
        .join(Ejemplar, Ejemplar.id == DetallePrestamo.ejemplar_id)
        .filter(
            Ejemplar.documento_id == documento.id,
            Prestamo.estado.in_(["activo", "vencido"])
        )
        .order_by(Prestamo.fecha_prestamo.desc())
        .first()
    )

    if not prestamo:
        raise HTTPException(status_code=404, detail="No hay préstamos activos o vencidos para ese ISBN")

    usuario = db.query(Usuario).filter(Usuario.id == prestamo.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario del préstamo no encontrado")

    ahora = datetime.now(timezone.utc)
    fecha_dev_est = prestamo.fecha_devolucion_estimada
    vencido = prestamo.estado == "vencido" or (fecha_dev_est and fecha_dev_est < ahora)

    estado_str = prestamo.estado.value if hasattr(prestamo.estado, "value") else prestamo.estado

    return {
        "prestamo": {
            "id": prestamo.id,
            "estado": estado_str,
            "fecha_prestamo": prestamo.fecha_prestamo,
            "fecha_devolucion_estimada": prestamo.fecha_devolucion_estimada,
        },
        "usuario": {
            "id": usuario.id,
            "rut": usuario.rut,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "email": usuario.email,
            "rol": usuario.rol,
            "sancionado": usuario.esta_sancionado(),
        },
        "documento": {
            "id": documento.id,
            "titulo": documento.titulo,
            "autor": documento.autor,
            "anio": documento.anio,
            "categoria": documento.categoria,
            "edicion": documento.edicion,
        },
        "vencido": vencido,
    }

@router.post("/registrar", response_model=PrestamoResponse)
def registrar_prestamo(data: PrestamoCreate, db: Session = Depends(get_db)):

    '''
    Registra un nuevo préstamo con sus detalles en el sistema.
    '''

    activos_count = db.query(Prestamo).filter(
        Prestamo.usuario_id == data.usuario_id,
        Prestamo.estado == 'activo'
    ).count()

    tiene_vencidos = db.query(Prestamo).filter(
        Prestamo.usuario_id == data.usuario_id,
        Prestamo.estado == 'vencido'
    ).count()

    if activos_count >= 3:
        raise HTTPException(status_code=400, detail=f"El usuario no puede realizar más préstamos, ya que tiene {activos_count} activos.")
    
    if tiene_vencidos > 0:
        raise HTTPException(status_code=400, detail="El usuario tiene préstamos vencidos y no puede realizar nuevos préstamos.")
    
    ejemplares = db.query(Ejemplar).filter(Ejemplar.id.in_(data.ejemplar_ids)).all()
    if len(ejemplares) != len(data.ejemplar_ids):
        raise HTTPException(status_code=404, detail="Uno o más ejemplares no existen.")
    for ejemplar in ejemplares:
        if ejemplar.estado != 'disponible':
            raise HTTPException(status_code=400, detail=f"El ejemplar {ejemplar.id} no está disponible para préstamo.")
        
    prestamo = Prestamo(
        tipo_prestamo=data.tipo_prestamo,
        usuario_id=data.usuario_id,
        bibliotecario_id=data.bibliotecario_id,
        fecha_prestamo=datetime.now(),
        hora_prestamo=datetime.now().time(),
        estado="activo"
    )
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)

    for ejemplar in ejemplares:
        detalle = DetallePrestamo(
            prestamo_id = prestamo.id,
            ejemplar_id = ejemplar.id
        )
        db.add(detalle)
        ejemplar.estado = 'prestado'

        fecha_estimada = calcular_fecha_devolucion(data.tipo_prestamo, ejemplar.tipo_documento)
        prestamo.fecha_devolucion_estimada = fecha_estimada
        prestamo.hora_devolucion_estimada = fecha_estimada.time()
    
    db.commit()
    db.refresh(prestamo)

    return prestamo

@router.get("/activos", response_model=PrestamoResponse)
def listar_prestamos_activos(
    usuario_id: Optional[int] = Query(None, description="ID del usuario para filtrar préstamos (opcional)"),
    page: int = Query(1, ge=1, description="Pagina de resultados (opcional)"),
    size: int = Query(20, ge=1, le=200, description="Número de resultados por página (opcional)"),
    db: Session = Depends(get_db)
):
    
    '''
    Lista los préstamos activos, con opción de filtrar por usuario y paginación.
    '''

    query = db.query(Prestamo).filter(Prestamo.estado == 'activo')

    if usuario_id is not None:
        query = query.filter(Prestamo.usuario_id == usuario_id)
    
    offset = (page - 1) * size
    
    prestamos = query.order_by(Prestamo.fecha_prestamo.desc()).offset(offset).limit(size).all()

    return prestamos

@router.get("/vencidos", response_model=List[PrestamoResponse])
def listar_prestamos_vencidos(db: Session = Depends(get_db)):

    '''
    Lista los préstamos a domicilio que han vencido y actualiza su estado a "vencido".
    '''

    hoy = datetime.now()
    prestamos = (
        db.query(Prestamo)
        .filter(
            Prestamo.tipo_prestamo == "domicilio",
            Prestamo.fecha_devolucion_estimada < hoy,
            Prestamo.estado == "activo"
        )
        .order_by(Prestamo.fecha_devolucion_estimada.asc())
        .all()
    )

    for p in prestamos:
        p.estado = "vencido"
    
    db.commit()

    return prestamos

@router.get("/sala-vencidos", response_model=List[PrestamoResponse])
def listar_prestamos_sala_vencidos(db: Session = Depends(get_db)):

    '''
    Lista los préstamos en sala que han vencido y actualiza su estado a "vencido".
    '''

    hoy = datetime.now()
    prestamos = (
        db.query(Prestamo)
        .filter(
            Prestamo.tipo_prestamo == "sala",
            Prestamo.fecha_devolucion_estimada < hoy,
            Prestamo.estado == "activo"
        )
        .order_by(Prestamo.fecha_devolucion_estimada.asc())
        .all()
    )

    for p in prestamos:
        p.estado = "vencido"
    
    db.commit()

    return prestamos

@router.patch("/{prestamo_id}/notificado")
def marcar_notificado(prestamo_id: int, db: Session = Depends(get_db)):

    '''
    Marca un préstamo vencido como notificado.
    '''

    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado.")
    
    if prestamo.estado != "vencido":
        raise HTTPException(status_code=400, detail="Solo se pueden notificar préstamos vencidos.")
    
    prestamo.notificado = True
    db.commit()

    return {"mensaje": f"Préstamo {prestamo_id} marcado como notificado."}

@router.post("/notificar-vencidos")
def verificacion_actualizacion_vencimientos(db: Session = Depends(get_db)):

    '''
    Verifica y actualiza el estado de los préstamos vencidos a "vencido".
    '''

    hoy = datetime.now()
    vencidos = db.query(Prestamo).filter(
        Prestamo.estado == "activo",
        Prestamo.fecha_devolucion_estimada < hoy
    ).all()

    for prestamo in vencidos:
        prestamo.estado = "vencido"
    
    db.commit()

    return {"mensaje": f"Se actualizaron {len(vencidos)} préstamos a vencido."}

@router.get("/usuarios/{usuario_id}/historial", response_model=List[PrestamoResponse])
def historial_prestamos_usuario(
    usuario_id: int,
    estado: str = Query(None, description="Filtrar por estado: activo, vencido o devuelto"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    
    '''
    Obtiene el historial de préstamos de un usuario con opción de filtrar por estado y paginación.
    '''

    query = db.query(Prestamo).filter(Prestamo.usuario_id == usuario_id)

    if estado:
        query = query.filter(Prestamo.estado == estado)

    offset = (page - 1) * size
    prestamos = (
        query.order_by(Prestamo.fecha_prestamo.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    if not prestamos:
        raise HTTPException(status_code=404, detail="No se encontraron préstamos para el usuario con los criterios especificados.")

    return prestamos

@router.get("/estadisticas", response_model=PrestamoStats)
def estadisticas_prestamos(db: Session = Depends(get_db)):

    '''
    Obtiene estadísticas sobre los préstamos.
    '''

    total_activos = db.query(Prestamo).filter(Prestamo.estado == "activo").count()
    total_vencidos = db.query(Prestamo).filter(Prestamo.estado == "vencido").count()
    total_devueltos = db.query(Prestamo).filter(Prestamo.estado == "devuelto").count()

    total_sala = db.query(Prestamo).filter(Prestamo.tipo_prestamo == "sala").count()
    total_domicilio = db.query(Prestamo).filter(Prestamo.tipo_prestamo == "domicilio").count()

    return PrestamoStats(
        total_activos=total_activos,
        total_vencidos=total_vencidos,
        total_devueltos=total_devueltos,
        total_sala=total_sala,
        total_domicilio=total_domicilio
    )
