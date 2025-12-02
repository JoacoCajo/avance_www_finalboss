from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.prestamos import Prestamo, DetallePrestamo
from app.models.ejemplar import Ejemplar
from app.schemas.devolucion import DevolucionRequest, DevolucionResponse
from app.utils.dates import calcular_fecha_devolucion

router = APIRouter(prefix="/devoluciones", tags=["Devoluciones"])

@router.post("/", response_model=DevolucionResponse)
def registrar_devolucion(data: DevolucionRequest, db: Session = Depends(get_db)):
    
    '''
    Registra la devolución de un ejemplar prestado.
    '''

    ejemplar = db.query(Ejemplar).filter(Ejemplar.codigo == data.ejemplar_codigo).first()
    if not ejemplar:
        raise HTTPException(status_code=404, detail="Ejemplar no encontrado")
    
    detalle = db.query(DetallePrestamo).join(Prestamo).filter(
        DetallePrestamo.ejemplar_id == ejemplar.id,
        Prestamo.estado == 'activo'
    ).first()

    if not detalle:
        raise HTTPException(status_code=404, detail="No hay un préstamo activo para este ejemplar")
    
    prestamo = db.query(Prestamo).filter(Prestamo.id == detalle.prestamo_id).first()

    ahora = datetime.now()
    prestamo.fecha_devolucion_real = ahora
    prestamo.hora_devolucion_real = ahora.time()

    ejemplar.estado = "devuelto"

    dias_atraso = 0
    if prestamo.fecha_devolucion_estimada and ahora.date() > prestamo.fecha_devolucion_estimada.date():
        dias_atraso = (ahora.date() - prestamo.fecha_devolucion_estimada.date()).days

    if dias_atraso > 0:
        dias_sancion = min(max(dias_atraso * 2, 3), 30)
        print(f"Sancion: {dias_sancion} dias por {dias_atraso} dias de atraso.")

    detalles_restantes = db.query(DetallePrestamo).join(Ejemplar).filter(
        DetallePrestamo.prestamo_id == prestamo.id,
        Ejemplar.estado != "devuelto"
    ).count()

    if detalles_restantes == 0:
        prestamo.estado = "devuelto"

    db.commit()
    db.refresh(prestamo)

    return DevolucionResponse(
        mensaje = "Devolución registrada exitosamente",
        ejemplar_codigo = ejemplar.codigo,
        dias_atraso = dias_atraso,
        estado_prestamo = prestamo.estado
    )