from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time

class PrestamoCreate(BaseModel):
    tipo_prestamo: str
    usuario_id: int
    bibliotecario_id: int
    ejemplares_ids: List[int]

class DetallePrestamoResponse(BaseModel):
    ejemplar_id: int

class PrestamoResponse(BaseModel):
    id: int 
    tipo_prestamo: str
    usuario_id: int
    bibliotecario_id: int
    fecha_prestamo: datetime
    fecha_devolucion_estimada: Optional[datetime]
    estado: str
    detalles: List[DetallePrestamoResponse] = []

    class Config:
        orm_mode = True

class PrestamoStats(BaseModel):
    total_activos: int
    total_vencidos: int
    total_devueltos: int
    total_salas: int
    total_domicilio: int