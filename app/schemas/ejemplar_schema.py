from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema para crear ejemplar
class EjemplarCreate(BaseModel):
    documento_id: int
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del ejemplar")
    ubicacion: str = Field(..., description="Ubicación en estantería, ej: A3-E2")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documento_id": 1,
                "codigo": "LIT-ESP-001-01",
                "ubicacion": "A3-E2"
            }
        }

# Schema para actualizar estado
class EjemplarEstadoUpdate(BaseModel):
    estado: str = Field(..., description="Nuevo estado del ejemplar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "estado": "prestado"
            }
        }

# Schema de respuesta
class EjemplarResponse(BaseModel):
    id: int
    documento_id: int
    codigo: str
    estado: str
    ubicacion: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schema para disponibilidad
class DisponibilidadResponse(BaseModel):
    disponibles: int
    prestados: int
    en_sala: int
    mantenimiento: int
    total: int
    puede_solicitar: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "disponibles": 3,
                "prestados": 2,
                "en_sala": 1,
                "mantenimiento": 0,
                "total": 6,
                "puede_solicitar": True
            }
        }


# Schema para historial
class HistorialEjemplarResponse(BaseModel):
    id: int
    ejemplar_id: int
    estado_anterior: Optional[str]
    estado_nuevo: str
    usuario_id: Optional[int]
    motivo: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True