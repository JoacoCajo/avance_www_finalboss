from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class LogNotificacion(Base):
    """
    Registro de todas las notificaciones enviadas.
    Útil para auditoría y evitar envíos duplicados.
    """
    __tablename__ = "log_notificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # validacion, recordatorio, confirmacion, etc.
    asunto = Column(String(255), nullable=False)
    destinatario = Column(String(120), nullable=False)
    enviado_exitosamente = Column(Boolean, default=False, nullable=False)
    error_mensaje = Column(Text, nullable=True)
    fecha_envio = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata adicional (JSON como texto)
    metadata_name = Column(Text, nullable=True)
    
    # Relación con usuario
    # usuario = relationship("Usuario", back_populates="notificaciones")
    
    @staticmethod
    def crear_log(usuario_id: int, tipo: str, asunto: str, destinatario: str, 
                  exitoso: bool = True, error: str = None):
        """Helper para crear un log de notificación"""
        return LogNotificacion(
            usuario_id=usuario_id,
            tipo=tipo,
            asunto=asunto,
            destinatario=destinatario,
            enviado_exitosamente=exitoso,
            error_mensaje=error
        )