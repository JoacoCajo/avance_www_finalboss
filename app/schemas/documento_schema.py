from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# ----------ESQUEMAS----------#

class DocumentoCrear(BaseModel):
    tipo: str
    titulo: str
    autor: str
    editorial: Optional[str] = None
    resumen: Optional[str] = None
    anio: Optional[int] = None
    edicion: Optional[str] = None
    categoria: Optional[str] = None
    tipo_medio: str
    existencias: Optional[int] = None
    disponible: Optional[bool] = True


class DocumentoOutput(DocumentoCrear):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ListaDocumentos(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_items: int
    items: List[DocumentoOutput]


class CategoriaConteo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    categoria: str
    conteo: int


class DocumentoActualizar(BaseModel):
    tipo: Optional[str] = None
    titulo: Optional[str] = None
    autor: Optional[str] = None
    editorial: Optional[str] = None
    resumen: Optional[str] = None
    anio: Optional[int] = None
    edicion: Optional[str] = None
    categoria: Optional[str] = None
    tipo_medio: Optional[str] = None
    existencias: Optional[int] = None
    disponible: Optional[bool] = None
