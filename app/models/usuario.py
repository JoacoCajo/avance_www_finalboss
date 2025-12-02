from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from passlib.context import CryptContext
from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(12), unique=True, nullable=False, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="usuario")
    activo = Column(Boolean, default=False, nullable=False)
    
    foto_url = Column(String(255), nullable=True)
    huella_hash = Column(String(255), nullable=True)
    fecha_sancion_hasta = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def set_password(self, password: str):
        """Hashear password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verificar password"""
        return pwd_context.verify(password, self.password_hash)
    
    def esta_sancionado(self) -> bool:
        """Verificar si está sancionado"""
        if self.fecha_sancion_hasta:
            return datetime.utcnow() < self.fecha_sancion_hasta
        return False
