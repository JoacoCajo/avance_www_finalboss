from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, LoginRequest, LoginResponse
from app.utils.validations import validar_rut, formatear_rut
from app.utils.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    
    # Validar RUT
    if not validar_rut(usuario_data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    rut_formateado = formatear_rut(usuario_data.rut)
    
    # Verificar RUT único
    if db.query(Usuario).filter(Usuario.rut == rut_formateado).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El RUT ya está registrado"
        )
    
    # Verificar email único
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    nuevo_usuario = Usuario(
        rut=rut_formateado,
        nombres=usuario_data.nombres,
        apellidos=usuario_data.apellidos,
        email=usuario_data.email.lower(),
        rol="usuario",  # Forzamos rol usuario
        activo=True     # Activación automática
    )
    nuevo_usuario.set_password(usuario_data.password)
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return {
        "success": True,
        "message": "Usuario registrado exitosamente. Pendiente de activación.",
        "data": {
            "id": nuevo_usuario.id,
            "rut": nuevo_usuario.rut,
            "nombres": nuevo_usuario.nombres,
            "apellidos": nuevo_usuario.apellidos,
            "email": nuevo_usuario.email,
            "rol": nuevo_usuario.rol,
            "activo": nuevo_usuario.activo
        }
    }

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión"""
    
    usuario = db.query(Usuario).filter(Usuario.email == login_data.email.lower()).first()
    
    if not usuario or not usuario.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    if usuario.esta_sancionado():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Usuario sancionado hasta {usuario.fecha_sancion_hasta}"
        )
    
    # Generar token
    access_token = create_access_token(
        data={"user_id": usuario.id, "rut": usuario.rut, "rol": usuario.rol}
    )
    
    return LoginResponse(
        success=True,
        message="Login exitoso",
        data={
            "token": access_token,
            "usuario": {
                "id": usuario.id,
                "rut": usuario.rut,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "email": usuario.email,
                "rol": usuario.rol,
                "activo": usuario.activo,
                "sancionado": usuario.esta_sancionado()
            }
        }
    )

@router.get("/me", response_model=dict)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Obtener usuario actual"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "rut": current_user.rut,
            "nombres": current_user.nombres,
            "apellidos": current_user.apellidos,
            "email": current_user.email,
            "rol": current_user.rol,
            "activo": current_user.activo,
            "foto_url": current_user.foto_url,
            "sancionado": current_user.esta_sancionado()
        }
    }
