from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional
import re

class UsuarioBase(BaseModel):
    rut: str = Field(..., min_length=9, max_length=12)
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    rol: Optional[str] = "usuario"
    
    @validator('rol')
    def validar_rol(cls, v):
        if v not in ['admin', 'usuario', 'guardia']:
            raise ValueError('Rol inválido')
        return v

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)

class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    foto_url: Optional[str] = None

class UsuarioResponse(BaseModel):
    id: int
    rut: str
    nombres: str
    apellidos: str
    email: str
    rol: str
    activo: bool
    foto_url: Optional[str]
    sancionado: bool
    fecha_sancion_hasta: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: dict

class TokenData(BaseModel):
    user_id: Optional[int] = None
    rut: Optional[str] = None
    rol: Optional[str] = None
