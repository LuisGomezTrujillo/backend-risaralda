"""
Módulo reutilizable para mapear los resultados de un sorteo (CSV) a las
celdas correspondientes del formato oficial de sorteo (Excel).

Este módulo es independiente de FastAPI: recibe listas de diccionarios
(ya parseadas del CSV) y una hoja de openpyxl, y escribe los valores.
Así se puede probar, reutilizar y mantener sin acoplarlo al framework web.
"""
import re
import unicodedata


def _normalizar(txt: str) -> str:
    """Mayúsculas, sin tildes, sin espacios repetidos — para comparar nombres de premios de forma robusta."""
    txt = txt.strip().upper()
    txt = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')
    txt = re.sub(r'\s+', ' ', txt)
    return txt


# --- Tabla superior "diseño del billete": tres bloques de secos numerados ---
# Cada bloque tiene su propia columna de NÚMERO y SERIE, y la fila del "Seco N"
# se calcula como fila_inicial + (N - 1).
BILLETE_SECOS = {
    'COSECHA MILLONARIA':   {'col_numero': 'K', 'col_serie': 'L', 'fila_inicial': 6},
    'DE PERLA':             {'col_numero': 'Q', 'col_serie': 'R', 'fila_inicial': 6},
    'TREBOL DE LA FORTUNA': {'col_numero': 'U', 'col_serie': 'V', 'fila_inicial': 6},
}

# --- Tabla inferior: premios especiales, cada uno con fila fija ---
PREMIOS_FILA_FIJA = {
    'PREMIO MAYOR': 21,
    'EL GORDO DE LA RISARALDA': 22,
    'ANGEL DE LA SUERTE': 23,
    'MULA MILLONARIA': 24,
    'MILAGRO MILLONARIO': 25,
    'ESCALERA MILLONARIA': 26,
    'GUACA DE ORO 3': 27,
    'GUACA DE ORO 2': 28,
    'GUACA DE ORO 1': 29,
    'COFRE DE DIAMANTES 5': 30,
    'COFRE DE DIAMANTES 4': 31,
    'COFRE DE DIAMANTES 3': 32,
    'COFRE DE DIAMANTES 2': 33,
    'COFRE DE DIAMANTES 1': 34,
}
COL_NUMERO_INFERIOR = 'P'
COL_SERIE_INFERIOR = 'S'

# El Premio Mayor gana fijo, sin serie (así lo indica el propio formato: "premio mayor sin serie gana fijo")
PREMIOS_SIN_SERIE = {'PREMIO MAYOR'}

# --- Bloque de pruebas ---
PRUEBAS_COL = 'G'
PRUEBAS_FILA_INICIAL = 23


def dividir_numero(numero_str: str):
    """Un ganador de 7 dígitos -> (número de 4 dígitos, serie de 3 dígitos), preservando ceros a la izquierda."""
    numero_str = str(numero_str).strip().zfill(7)
    return numero_str[:4], numero_str[4:]


def procesar_resultados(ws, filas):
    """
    filas: lista de dicts con llaves 'Premio', 'Numero Ganador' (del CSV de Resultados).
    Escribe NÚMERO y SERIE en las celdas correspondientes de la hoja `ws` (openpyxl).
    Devuelve la lista de nombres de premio que no se pudieron ubicar en el formato.
    """
    no_encontrados = []
    for fila in filas:
        premio_raw = fila['Premio']
        numero = fila['Numero Ganador']
        premio_norm = _normalizar(premio_raw)
        premio_sin_seco = re.sub(r'^SECO\s+', '', premio_norm)

        # 1) ¿Es un seco numerado de la tabla superior (billete)?
        ubicado = False
        for nombre, cfg in BILLETE_SECOS.items():
            if premio_sin_seco.startswith(nombre):
                resto = premio_sin_seco[len(nombre):].strip()
                if resto.isdigit():
                    fila_excel = cfg['fila_inicial'] + (int(resto) - 1)
                    num, serie = dividir_numero(numero)
                    ws[f"{cfg['col_numero']}{fila_excel}"] = num
                    ws[f"{cfg['col_serie']}{fila_excel}"] = serie
                    ubicado = True
                break
        if ubicado:
            continue

        # 2) ¿Es un premio de fila fija (tabla inferior)?
        clave = premio_sin_seco if premio_sin_seco in PREMIOS_FILA_FIJA else premio_norm
        if clave in PREMIOS_FILA_FIJA:
            fila_excel = PREMIOS_FILA_FIJA[clave]
            num, serie = dividir_numero(numero)
            ws[f"{COL_NUMERO_INFERIOR}{fila_excel}"] = num
            if clave not in PREMIOS_SIN_SERIE:
                ws[f"{COL_SERIE_INFERIOR}{fila_excel}"] = serie
            continue

        no_encontrados.append(premio_raw)
    return no_encontrados


def procesar_pruebas(ws, filas):
    """
    filas: lista de dicts con llaves 'Prueba', 'Numero Ganador' (del CSV de Pruebas).
    Escribe el número de cada prueba en su celda. Devuelve las pruebas no ubicadas.
    """
    no_encontrados = []
    for fila in filas:
        prueba_raw = fila['Prueba']
        numero = fila['Numero Ganador']
        m = re.search(r'(\d+)', prueba_raw)
        if not m:
            no_encontrados.append(prueba_raw)
            continue
        idx = int(m.group(1))
        fila_excel = PRUEBAS_FILA_INICIAL + (idx - 1)
        ws[f'{PRUEBAS_COL}{fila_excel}'] = str(numero).strip()
    return no_encontrados