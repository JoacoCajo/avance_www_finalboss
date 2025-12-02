import re

def validar_rut(rut: str) -> bool:
    """Valida RUT chileno"""
    rut = rut.replace(".", "").replace("-", "")
    
    if not re.match(r'^\d{7,8}[0-9Kk]$', rut):
        return False
    
    rut_num = rut[:-1]
    dv = rut[-1].upper()
    
    suma = 0
    multiplo = 2
    
    for digit in reversed(rut_num):
        suma += int(digit) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    return dv == dv_calculado

def formatear_rut(rut: str) -> str:
    """Formatea RUT"""
    rut = rut.replace(".", "").replace("-", "")
    return f"{rut[:-1]}-{rut[-1]}"