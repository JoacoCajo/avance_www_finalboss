# app/models/__init__.py
"""
Importar todos los modelos aquí para que SQLAlchemy los conozca.
"""

from app.models.usuario import Usuario
from app.models.ejemplar import Ejemplar
from app.models.historial_ejemplar import HistorialEjemplar
from app.models.documento import Documento

# ROL 5
try:
    from app.models.reserva import Reserva
    from app.models.token_validacion import TokenValidacion
    from app.models.log_notificaciones import LogNotificacion
except ImportError:
    pass

# ROL 4
try:
    from app.models.prestamos import Prestamo
except ImportError:
    pass

__all__ = [
    "Usuario",
    "Ejemplar", 
    "HistorialEjemplar",
    "Reserva",
    "Documento"
    "TokenValidacion",
    "LogNotificacion",
    "Prestamo"
]