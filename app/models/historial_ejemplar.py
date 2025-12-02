from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class HistorialEjemplar(Base):
    """
    Registro de todos los cambios de estado de un ejemplar.
    Útil para auditoría y trazabilidad.
    """
    __tablename__ = "historial_ejemplares"
    
    id = Column(Integer, primary_key=True, index=True)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False, index=True)
    estado_anterior = Column(String(20), nullable=True)
    estado_nuevo = Column(String(20), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Quién hizo el cambio
    motivo = Column(Text, nullable=True)  # Razón del cambio (opcional)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    # ejemplar = relationship("Ejemplar", back_populates="historial")
    # usuario = relationship("Usuario")