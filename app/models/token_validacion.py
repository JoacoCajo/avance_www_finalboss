from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base
import uuid

class TokenValidacion(Base):
    """
    Tokens para validación de correo electrónico.
    Se generan al registrar un usuario y expiran en 24 horas.
    """
    __tablename__ = "tokens_validacion"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(100), unique=True, nullable=False, index=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con usuario
    # usuario = relationship("Usuario", back_populates="tokens")
    
    @staticmethod
    def generar_token():
        """Generar token único UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def crear_token(usuario_id: int, horas_expiracion: int = 24):
        """Crear nuevo token con expiración"""
        return TokenValidacion(
            usuario_id=usuario_id,
            token=TokenValidacion.generar_token(),
            fecha_expiracion=datetime.utcnow() + timedelta(hours=horas_expiracion)
        )
    
    def esta_expirado(self) -> bool:
        """Verificar si el token está expirado"""
        return datetime.utcnow() > self.fecha_expiracion
    
    def es_valido(self) -> bool:
        """Verificar si el token es válido (no usado y no expirado)"""
        return not self.usado and not self.esta_expirado()