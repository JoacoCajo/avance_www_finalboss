from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from typing import Optional

class ReservaCreate(BaseModel):
    """Schema para crear una reserva"""
    documento_id: int = Field(..., gt=0, description="ID del documento a reservar")
    fecha_reserva: date = Field(..., description="Fecha para la que se reserva (formato: YYYY-MM-DD)")
    
    @validator('fecha_reserva')
    def validar_fecha_futura(cls, v):
        """La fecha de reserva debe ser al menos mañana"""
        hoy = date.today()
        if v <= hoy:
            raise ValueError('La fecha de reserva debe ser al menos para mañana')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "documento_id": 1,
                "fecha_reserva": "2025-11-01"
            }
        }

class ReservaResponse(BaseModel):
    """Schema de respuesta de reserva"""
    id: int
    usuario_id: int
    documento_id: int
    fecha_reserva: date
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    motivo_cancelacion: Optional[str]
    
    class Config:
        from_attributes = True

class ReservaCancelar(BaseModel):
    """Schema para cancelar una reserva"""
    motivo: Optional[str] = Field(None, max_length=255, description="Motivo de cancelación (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "motivo": "Ya no necesito el documento"
            }
        }

class ReservaConDocumento(BaseModel):
    """Reserva con información del documento"""
    id: int
    usuario_id: int
    documento_id: int
    documento_titulo: str
    documento_autor: str
    fecha_reserva: date
    estado: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True