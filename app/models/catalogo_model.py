from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from typing import List, Tuple
from app.models.documento import Documento

# --- LÓGICA DE BD PARA 'Catalogo' y 'Categorias' (Búsquedas y Listados) ---
# Refactorizado para usar SQLAlchemy ORM en lugar de psycopg2

def listar_documentos(db: Session, page: int, size: int) -> Tuple[List[Documento], int]:
    """
    Lista todos los documentos activos con paginación.
    
    Args:
        db: Sesión de SQLAlchemy
        page: Número de página (empezando en 1)
        size: Cantidad de elementos por página
    
    Returns:
        Tupla con (lista de documentos, total de items)
    """
    try:
        offset = (page - 1) * size
        
        # Contar total de documentos activos
        total_items = db.query(func.count(Documento.id)).filter(
            Documento.activo == True
        ).scalar()
        
        # Obtener documentos paginados
        documentos = db.query(Documento).filter(
            Documento.activo == True
        ).order_by(Documento.id).offset(offset).limit(size).all()
        
        return documentos, total_items
    
    except Exception as e:
        print(f"Error en DB (listar_documentos): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al listar documentos"
        )


def busqueda_basica(db: Session, busqueda: str, page: int, size: int) -> Tuple[List[Documento], int]:
    """
    Búsqueda básica por título o autor (case insensitive).
    
    Args:
        db: Sesión de SQLAlchemy
        busqueda: Término de búsqueda
        page: Número de página
        size: Cantidad de elementos por página
    
    Returns:
        Tupla con (lista de documentos, total de items)
    """
    try:
        offset = (page - 1) * size
        termino_ilike = f"%{busqueda}%"
        
        # Crear query base con filtros
        query_base = db.query(Documento).filter(
            Documento.activo == True,
            (Documento.titulo.ilike(termino_ilike) | 
             Documento.autor.ilike(termino_ilike))
        )
        
        # Contar total de resultados
        total_items = query_base.count()
        
        # Obtener resultados paginados
        documentos = query_base.order_by(
            Documento.id
        ).offset(offset).limit(size).all()
        
        return documentos, total_items
    
    except Exception as e:
        print(f"Error en DB (busqueda_basica): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno en búsqueda básica"
        )


def lista_categorias(db: Session) -> List[dict]:
    """
    Lista todas las categorías con su conteo de documentos.
    
    Args:
        db: Sesión de SQLAlchemy
    
    Returns:
        Lista de diccionarios con categoría y conteo
    """
    try:
        # Agrupar por categoría y contar
        resultados = db.query(
            Documento.categoria,
            func.count(Documento.id).label('conteo')
        ).filter(
            Documento.activo == True,
            Documento.categoria.isnot(None)
        ).group_by(
            Documento.categoria
        ).order_by(
            Documento.categoria.asc()
        ).all()
        
        # Convertir a lista de diccionarios
        categorias = [
            {"categoria": cat, "conteo": count} 
            for cat, count in resultados
        ]
        
        return categorias
    
    except Exception as e:
        print(f"Error en DB (lista_categorias): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al listar categorías"
        )


def documento_por_categoria(db: Session, categoria: str, page: int, size: int) -> Tuple[List[Documento], int]:
    """
    Lista documentos filtrados por categoría con paginación.
    
    Args:
        db: Sesión de SQLAlchemy
        categoria: Categoría a filtrar
        page: Número de página
        size: Cantidad de elementos por página
    
    Returns:
        Tupla con (lista de documentos, total de items)
    """
    try:
        offset = (page - 1) * size
        
        # Crear query base con filtro de categoría
        query_base = db.query(Documento).filter(
            Documento.activo == True,
            Documento.categoria == categoria
        )
        
        # Contar total de resultados
        total_items = query_base.count()
        
        # Obtener resultados paginados
        documentos = query_base.order_by(
            Documento.id
        ).offset(offset).limit(size).all()
        
        return documentos, total_items
    
    except Exception as e:
        print(f"Error en DB (documento_por_categoria): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al listar por categoría"
        )


def busqueda_avanzada(
    db: Session,
    tipo: str = None,
    categoria: str = None,
    autor: str = None,
    año_desde: int = None,
    año_hasta: int = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Documento], int]:
    """
    Búsqueda avanzada con múltiples filtros opcionales.
    
    Args:
        db: Sesión de SQLAlchemy
        tipo: Tipo de documento (libro, audio, video, revista)
        categoria: Categoría del documento
        autor: Autor (búsqueda parcial)
        año_desde: Año mínimo de publicación
        año_hasta: Año máximo de publicación
        page: Número de página
        size: Cantidad de elementos por página
    
    Returns:
        Tupla con (lista de documentos, total de items)
    """
    try:
        offset = (page - 1) * size
        
        # Query base
        query_base = db.query(Documento).filter(Documento.activo == True)
        
        # Aplicar filtros opcionales
        if tipo:
            query_base = query_base.filter(Documento.tipo == tipo)
        
        if categoria:
            query_base = query_base.filter(Documento.categoria == categoria)
        
        if autor:
            query_base = query_base.filter(
                Documento.autor.ilike(f"%{autor}%")
            )
        
        if año_desde:
            query_base = query_base.filter(Documento.año >= año_desde)
        
        if año_hasta:
            query_base = query_base.filter(Documento.año <= año_hasta)
        
        # Contar total
        total_items = query_base.count()
        
        # Obtener resultados paginados
        documentos = query_base.order_by(
            Documento.id
        ).offset(offset).limit(size).all()
        
        return documentos, total_items
    
    except Exception as e:
        print(f"Error en DB (busqueda_avanzada): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno en búsqueda avanzada"
        )


def obtener_estadisticas(db: Session) -> dict:
    """
    Obtiene estadísticas generales del catálogo.
    
    Args:
        db: Sesión de SQLAlchemy
    
    Returns:
        Diccionario con estadísticas
    """
    try:
        # Total de documentos activos
        total_documentos = db.query(func.count(Documento.id)).filter(
            Documento.activo == True
        ).scalar()
        
        # Documentos por tipo
        por_tipo = db.query(
            Documento.tipo,
            func.count(Documento.id).label('cantidad')
        ).filter(
            Documento.activo == True
        ).group_by(Documento.tipo).all()
        
        # Total de categorías
        total_categorias = db.query(
            func.count(func.distinct(Documento.categoria))
        ).filter(
            Documento.activo == True,
            Documento.categoria.isnot(None)
        ).scalar()
        
        estadisticas = {
            "total_documentos": total_documentos,
            "total_categorias": total_categorias,
            "por_tipo": {tipo: cantidad for tipo, cantidad in por_tipo}
        }
        
        return estadisticas
    
    except Exception as e:
        print(f"Error en DB (obtener_estadisticas): {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al obtener estadísticas"
        )