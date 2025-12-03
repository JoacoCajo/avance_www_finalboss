from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Time, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TipoPrestamo(enum.Enum):
    sala = "sala"
    domicilio = "domicilio"

class EstadoPrestamo(enum.Enum):
    activo = "activo"
    devuelto = "devuelto"
    vencido = "vencido"

class Prestamo(Base): 
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    tipo_prestamo = Column(Enum(TipoPrestamo), nullable=False)
    isbn_asociado = Column(String(50), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    biblioteca_id = Column(Integer, ForeignKey("bibliotecas.id"), nullable=False)
    fecha_prestamo = Column(DateTime, nullable=False)
    hora_prestamo = Column(Time, nullable=False)
    fecha_devolucion_estimada = Column(DateTime, nullable=True)
    hora_devolucion_estimada = Column(Time, nullable=True)
    fecha_devolucion_real = Column(DateTime, nullable=True)
    hora_devolucion_real = Column(Time, nullable=True)
    estado = Column(Enum(EstadoPrestamo), default=EstadoPrestamo.activo)
    notificado = Column(Boolean, default=False)

    detalles = relationship("DetallePrestamo", back_populates="prestamo")

class DetallePrestamo(Base):
    __tablename__ = "detalles_prestamo"

    id = Column(Integer, primary_key=True, index=True)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False)

    prestamo = relationship("Prestamo", back_populates="detalles")
