from pydantic import BaseModel
from typing import Optional

class DevolucionRequest(BaseModel):
    ejemplar_codigo : str

class DevolucionResponse(BaseModel):
    mensaje: str
    ejemplar_codigo: str
    dias_atraso: Optional[int] = 0
    estado_prestamo: str