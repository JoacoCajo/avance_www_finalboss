from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Documento(Base):
    """
    Catálogo de documentos de la biblioteca.
    Este modelo lo maneja ROL 2, pero lo necesitas para relaciones.
    """
    __tablename__ = "documentos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)  # libro, audio, video, revista
    titulo = Column(String(255), nullable=False, index=True)
    autor = Column(String(255), nullable=False)
    editorial = Column(String(100), nullable=True)
    anio = Column(Integer, nullable=True)
    edicion = Column(String(50), nullable=True)
    categoria = Column(String(100), nullable=True, index=True)
    tipo_medio = Column(String(50), nullable=True)  # fisico, digital, cd, dvd, etc.
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones (serán definidas por ROL 2 y ROL 3)
    # ejemplares = relationship("Ejemplar", back_populates="documento")
    # reservas = relationship("Reserva", back_populates="documento")