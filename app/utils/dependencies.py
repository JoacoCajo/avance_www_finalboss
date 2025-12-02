from fastapi import HTTPException
from typing import Optional

# --- LÓGICA DE VALIDACIÓN DE CATEGORÍA ---
CATEGORIAS_VALIDAS={
    "literatura_chilena",
    "tecnico_español",
    "novela",
    "ciencia_ficcion",
    "historia",
    "infantil",
    "accion",
    "guerra",
    "romance"
    #podemos agregar más!
} 

def validacion_categoria(categoria:Optional[str]):
    """
    Valida si una categoría está en la lista de categorías permitidas.
    Lanza una excepción HTTP 400 si no es válida.
    """
    if categoria is None:
        return True # Es válida porque es opcional
    
    # Es mejor práctica lanzar la excepción aquí mismo
    if categoria not in CATEGORIAS_VALIDAS:
        raise HTTPException(
            status_code=400, # 400 Bad Request
            detail=f"Categoria '{categoria}' no es valida."
        )
    return True

# --- LÓGICA DE SEGURIDAD (Placeholder) ---
async def verificacion():
    """
    Placeholder para la dependencia de seguridad que verifica el rol.
    """
    print("Verificando rol")
    '''
    Lógica de verificación.
    '''
    return True
