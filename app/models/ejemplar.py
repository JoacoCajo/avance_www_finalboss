from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Ejemplar(Base):
    __tablename__ = "ejemplares"
    
    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    estado = Column(String(20), default="disponible")  # disponible, prestado, en_sala, devuelto, mantenimiento
    ubicacion = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con documento (ROL 2 lo define)
    # documento = relationship("Documento", back_populates="ejemplares")