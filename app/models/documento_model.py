from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional
from app.models.documento import Documento

# --- LÓGICA DE BD PARA EL RECURSO 'Documentos' (CRUD) ---
# Refactorizado para usar SQLAlchemy ORM en lugar de psycopg2

def ingresar_documento(db: Session, data: dict) -> Documento:
    """
    Crea un nuevo documento en la BD usando SQLAlchemy.
    
    Args:
        db: Sesión de SQLAlchemy
        data: Diccionario con los datos del documento
    
    Returns:
        Documento: El objeto Documento creado
    """
    try:
        # Evitar enviar columnas generadas
        data = {k: v for k, v in data.items() if k != "disponible"}

        nuevo_documento = Documento(
            tipo=data.get('tipo'),
            titulo=data.get('titulo'),
            autor=data.get('autor'),
            editorial=data.get('editorial'),
            resumen=data.get('resumen'),
            link=data.get('link'),
            anio=data.get('anio'),
            edicion=data.get('edicion'),
            categoria=data.get('categoria'),
            tipo_medio=data.get('tipo_medio'),
            existencias=data.get('existencias')
        )
        
        db.add(nuevo_documento)
        db.commit()
        db.refresh(nuevo_documento)
        
        print(f"Ingreso a la bd correcto, nuevo ID: {nuevo_documento.id}")
        return nuevo_documento
    
    except Exception as e:
        print(f"Error en DB (ingresar_documento): {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al crear el documento: {str(e)}"
        )


def busqueda_por_id(db: Session, documento_id: int) -> Optional[Documento]:
    """
    Busca un documento por su ID.
    
    Args:
        db: Sesión de SQLAlchemy
        documento_id: ID del documento a buscar
    
    Returns:
        Documento o None si no existe
    """
    try:
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        
        return documento
    
    except Exception as e:
        print(f"Error en DB (busqueda_por_id): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al buscar documento por ID"
        )

def busqueda_por_isbn(db: Session, isbn: str) -> Optional[Documento]:
    """
    Busca un documento por su ISBN (campo edicion).
    """
    try:
        documento = db.query(Documento).filter(Documento.edicion == isbn).first()
        return documento
    except Exception as e:
        print(f"Error en DB (busqueda_por_isbn): {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al buscar documento por ISBN"
        )


def actualizar_documento(db: Session, id: int, data: dict) -> Optional[Documento]:
    """
    Actualiza un documento existente.
    
    Args:
        db: Sesión de SQLAlchemy
        id: ID del documento a actualizar
        data: Diccionario con los campos a actualizar
    
    Returns:
        Documento actualizado o None si no existe
    """
    try:
        documento = db.query(Documento).filter(Documento.id == id).first()
        
        if documento is None:
            return None
        
        # Actualizar solo los campos que vienen en data
        for key, value in data.items():
            field_name = 'anio' if key == 'anio' else key
            
            if hasattr(documento, field_name):
                setattr(documento, field_name, value)
        
        db.commit()
        db.refresh(documento)
        
        print(f"Documento {id} actualizado exitosamente")
        return documento
    
    except Exception as e:
        print(f"Error en DB (actualizar_documento): {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Error interno al actualizar el documento"
        )


def eliminar_documento(db: Session, id: int) -> bool:
    """
    Elimina un documento de forma permanente.
    
    Args:
        db: Sesión de SQLAlchemy
        id: ID del documento a eliminar
    
    Returns:
        True si se eliminó, False si no existía
    """
    try:
        documento = db.query(Documento).filter(Documento.id == id).first()
        
        if documento is None:
            return False
        
        db.delete(documento)
        db.commit()
        
        print(f"Documento {id} eliminado")
        return True
    
    except Exception as e:
        print(f"Error en DB (eliminar_documento): {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Error interno al eliminar el documento"
        )


def listar_documentos(
    db: Session, 
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Documento]:
    """
    Lista documentos con filtros opcionales.
    
    Args:
        db: Sesión de SQLAlchemy
        tipo: Filtrar por tipo (libro, audio, video, revista)
        categoria: Filtrar por categoría
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        Lista de Documentos
    """
    try:
        query = db.query(Documento)
        
        if tipo:
            query = query.filter(Documento.tipo == tipo)
        
        if categoria:
            query = query.filter(Documento.categoria == categoria)
        
        documentos = query.offset(skip).limit(limit).all()
        
        return documentos
    
    except Exception as e:
        print(f"Error en DB (listar_documentos): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al listar documentos"
        )


def buscar_documentos(
    db: Session,
    termino: str,
    skip: int = 0,
    limit: int = 100
) -> list[Documento]:
    """
    Busca documentos por título o autor (búsqueda parcial).
    
    Args:
        db: Sesión de SQLAlchemy
        termino: Término de búsqueda
        skip: Número de registros a saltar
        limit: Número máximo de registros
    
    Returns:
        Lista de Documentos que coinciden
    """
    try:
        termino_busqueda = f"%{termino}%"
        
        documentos = db.query(Documento).filter(
            (Documento.titulo.ilike(termino_busqueda) | 
             Documento.autor.ilike(termino_busqueda))
        ).offset(skip).limit(limit).all()
        
        return documentos
    
    except Exception as e:
        print(f"Error en DB (buscar_documentos): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al buscar documentos"
        )
