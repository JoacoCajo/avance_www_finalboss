from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Reserva(Base):
    """
    Reservas de documentos por parte de usuarios.
    Permite reservar un documento para una fecha futura.
    """
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False, index=True)
    fecha_reserva = Column(Date, nullable=False)  # Fecha para la que se reserva
    estado = Column(String(20), default="pendiente", nullable=False)  # pendiente, activa, cancelada, completada
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)
    motivo_cancelacion = Column(String(255), nullable=True)
    
    # Relaciones
    # usuario = relationship("Usuario", back_populates="reservas")
    # documento = relationship("Documento", back_populates="reservas")
    
    def puede_cancelar(self) -> bool:
        """Verificar si la reserva puede ser cancelada"""
        return self.estado in ["pendiente", "activa"]
    
    def esta_activa(self) -> bool:
        """Verificar si la reserva está activa"""
        return self.estado == "activa"