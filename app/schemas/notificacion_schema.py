from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class EmailRequest(BaseModel):
    """Request para enviar email genérico"""
    destinatario: EmailStr
    asunto: str
    mensaje: str
    html: Optional[bool] = True

class NotificacionLog(BaseModel):
    """Schema para log de notificación"""
    id: int
    usuario_id: int
    tipo: str
    asunto: str
    destinatario: str
    enviado_exitosamente: bool
    error_mensaje: Optional[str]
    fecha_envio: datetime
    
    class Config:
        from_attributes = True

class RecordatorioPrestamoVencido(BaseModel):
    """Datos para recordatorio de préstamo vencido"""
    prestamo_id: int
    documento_titulo: str
    fecha_devolucion: datetime
    dias_atraso: int

class RecordatorioRequest(BaseModel):
    """Request para enviar recordatorios masivos"""
    usuario_rut: Optional[str] = None  # Si se especifica, solo a ese usuario
    tipo_prestamo: Optional[str] = None  # domicilio, sala
    enviar_ahora: bool = True

class NotificacionResponse(BaseModel):
    """Respuesta de envío de notificaciones"""
    success: bool
    total_enviados: int
    total_fallidos: int
    detalles: List[dict]
    mensaje: str