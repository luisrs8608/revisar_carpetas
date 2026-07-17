import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from rapidfuzz import fuzz, process

from minutos import es_minutos_inf_valido
from salida_excel import asegurar_extension_xlsx, exportar_excel


# ============================================================
# CONFIGURACIÓN
# ============================================================

DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
ARCHIVO_CONFIGURACION = DIRECTORIO_PROYECTO / "config.json"


@dataclass(frozen=True)
class Configuracion:
    directorio_principal: Path
    archivo_credenciales: Path
    google_sheet_id: str
    nombre_hoja: str
    fila_encabezados: int
    fila_inicial_datos: int
    archivo_salida: Path
    umbral_coincidencia_probable: int
    umbral_revision_manual: int


def resolver_ruta(valor: str, base: Path = DIRECTORIO_PROYECTO) -> Path:
    """
    Convierte rutas relativas o con ~ en rutas absolutas.
    """
    ruta = Path(str(valor)).expanduser()

    if not ruta.is_absolute():
        ruta = base / ruta

    return ruta


def cargar_configuracion() -> Configuracion:
    """
    Lee config.json para evitar editar este script en cada instalación.
    """
    if not ARCHIVO_CONFIGURACION.exists():
        raise FileNotFoundError(
            "No se encontró config.json. Copia config.example.json como "
            "config.json y completa los valores de tu entorno."
        )

    with ARCHIVO_CONFIGURACION.open(encoding="utf-8") as archivo:
        datos = json.load(archivo)

    campos_requeridos = [
        "directorio_principal",
        "archivo_credenciales",
        "google_sheet_id",
        "nombre_hoja",
        "fila_encabezados",
        "fila_inicial_datos",
    ]

    campos_faltantes = [
        campo
        for campo in campos_requeridos
        if not datos.get(campo)
    ]

    if campos_faltantes:
        raise ValueError(
            "Faltan valores obligatorios en config.json: "
            f"{', '.join(campos_faltantes)}"
        )

    directorio_principal = resolver_ruta(datos["directorio_principal"])

    archivo_salida = Path(
        str(datos.get(
            "archivo_salida",
            "resultado_comparacion_carpetas.xlsx"
        ))
    ).expanduser()

    archivo_salida = asegurar_extension_xlsx(archivo_salida)

    if not archivo_salida.is_absolute():
        archivo_salida = directorio_principal / archivo_salida

    return Configuracion(
        directorio_principal=directorio_principal,
        archivo_credenciales=resolver_ruta(datos["archivo_credenciales"]),
        google_sheet_id=str(datos["google_sheet_id"]).strip(),
        nombre_hoja=str(datos["nombre_hoja"]).strip(),
        fila_encabezados=int(datos["fila_encabezados"]),
        fila_inicial_datos=int(datos["fila_inicial_datos"]),
        archivo_salida=archivo_salida,
        umbral_coincidencia_probable=int(
            datos.get("umbral_coincidencia_probable", 90)
        ),
        umbral_revision_manual=int(
            datos.get("umbral_revision_manual", 75)
        ),
    )


CONFIGURACION = cargar_configuracion()

DIRECTORIO_PRINCIPAL = CONFIGURACION.directorio_principal
ARCHIVO_CREDENCIALES = CONFIGURACION.archivo_credenciales
GOOGLE_SHEET_ID = CONFIGURACION.google_sheet_id
NOMBRE_HOJA = CONFIGURACION.nombre_hoja
FILA_ENCABEZADOS = CONFIGURACION.fila_encabezados
FILA_INICIAL_DATOS = CONFIGURACION.fila_inicial_datos

# Se leerán las columnas A a K:
# A = FECHA
# B = NOMBRE
# K = MINUTOS INF
RANGO_LECTURA = f"A{FILA_ENCABEZADOS}:K"

# Archivo final.
ARCHIVO_SALIDA = CONFIGURACION.archivo_salida

# Umbrales de similitud.
# 100 = coincidencia exacta después de normalizar.
# 90+ = coincidencia muy probable.
# 75-89 = posible coincidencia, conviene revisar manualmente.
# Menos de 75 = no encontrado.
UMBRAL_COINCIDENCIA_PROBABLE = CONFIGURACION.umbral_coincidencia_probable
UMBRAL_REVISION_MANUAL = CONFIGURACION.umbral_revision_manual


# ============================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================

def quitar_tildes(texto: str) -> str:
    """
    Elimina tildes y caracteres diacríticos.

    Ejemplo:
    'María González' -> 'Maria Gonzalez'
    """
    texto_normalizado = unicodedata.normalize("NFD", texto)

    return "".join(
        caracter
        for caracter in texto_normalizado
        if unicodedata.category(caracter) != "Mn"
    )


def normalizar_nombre(texto: str) -> str:
    """
    Normaliza un nombre para comparar.

    Ejemplos:
    'Juan_Perez'       -> 'juan perez'
    'Juan-Perez'       -> 'juan perez'
    'JUAN  PÉREZ'      -> 'juan perez'
    ' Juan.Perez '     -> 'juan perez'
    """
    if not texto:
        return ""

    texto = str(texto).strip()
    texto = quitar_tildes(texto).lower()

    # Convertir guiones y guiones bajos en espacios.
    texto = re.sub(r"[_-]+", " ", texto)

    # Eliminar puntuación restante.
    texto = re.sub(r"[^\w\s]", " ", texto)

    # Reemplazar espacios repetidos.
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_nombre_ordenado(texto: str) -> str:
    """
    Normaliza un nombre y ordena sus palabras alfabéticamente.

    Esto permite considerar iguales:
    'Juan Perez' y 'Perez Juan'
    """
    nombre = normalizar_nombre(texto)

    palabras = nombre.split()

    return " ".join(sorted(palabras))


# ============================================================
# LECTURA DE GOOGLE SHEETS
# ============================================================

def obtener_datos_google_sheet() -> list[dict]:
    """
    Lee la pestaña desde la fila 11.

    La fila 11 se usa como encabezado.
    La fila 12 en adelante se interpreta como registros.
    """

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    credentials = Credentials.from_service_account_file(
        ARCHIVO_CREDENCIALES,
        scopes=scopes
    )

    cliente = gspread.authorize(credentials)

    spreadsheet = cliente.open_by_key(GOOGLE_SHEET_ID)
    worksheet = spreadsheet.worksheet(NOMBRE_HOJA)

    valores = worksheet.get(RANGO_LECTURA)

    if not valores:
        raise ValueError(
            f"No se encontraron datos en el rango {RANGO_LECTURA}."
        )

    encabezados = valores[0]

    encabezados_normalizados = [
        normalizar_nombre(encabezado)
        for encabezado in encabezados
    ]

    columnas_requeridas = {
        "fecha": None,
        "nombre": None,
        "minutos inf": None,
    }

    for indice, encabezado in enumerate(encabezados_normalizados):
        if encabezado in columnas_requeridas:
            columnas_requeridas[encabezado] = indice

    columnas_faltantes = [
        columna
        for columna, indice in columnas_requeridas.items()
        if indice is None
    ]

    if columnas_faltantes:
        raise ValueError(
            "No se encontraron estas columnas en la fila "
            f"{FILA_ENCABEZADOS}: {', '.join(columnas_faltantes)}.\n"
            f"Encabezados encontrados: {encabezados}"
        )

    indice_fecha = columnas_requeridas["fecha"]
    indice_nombre = columnas_requeridas["nombre"]
    indice_minutos_inf = columnas_requeridas["minutos inf"]

    registros = []
    fecha_actual = ""

    # Comenzamos en la segunda fila del resultado,
    # que representa la fila 12 de Google Sheets.
    for numero_fila_sheet, fila in enumerate(
        valores[1:],
        start=FILA_INICIAL_DATOS
    ):
        # Completar columnas faltantes para evitar errores de índice.
        fila = fila + [""] * (len(encabezados) - len(fila))

        fecha_fila = fila[indice_fecha].strip()
        nombre_original = fila[indice_nombre].strip()
        valor_minutos_inf = fila[indice_minutos_inf]
        minutos_inf = (
            str(valor_minutos_inf).strip()
            if valor_minutos_inf is not None
            else ""
        )
        minutos_inf_valido = es_minutos_inf_valido(minutos_inf)

        if fecha_fila:
            fecha_actual = fecha_fila

        # Ignorar filas sin nombre.
        if not nombre_original:
            continue

        registros.append({
            "FilaGoogleSheet": numero_fila_sheet,
            "FechaOriginalGoogleSheet": fecha_actual,
            "NombreGoogleSheet": nombre_original,
            "NombreNormalizadoGoogleSheet": normalizar_nombre(nombre_original),
            "NombreOrdenadoGoogleSheet": normalizar_nombre_ordenado(
                nombre_original
            ),
            "MinutosInf": minutos_inf,
            "MinutosInfValido": minutos_inf_valido,
            "TieneMinutosInf": "Sí" if minutos_inf_valido else "No",
        })

    return registros


# ============================================================
# BÚSQUEDA Y COMPARACIÓN DE NOMBRES
# ============================================================

def buscar_mejor_coincidencia(
    nombre_carpeta: str,
    registros_sheet: list[dict]
) -> dict:
    """
    Busca el nombre más parecido de Google Sheets.

    Primero compara el nombre normalizado y ordenado, para manejar
    cambios de posición como:
    'Juan Perez' <-> 'Perez Juan'.

    Luego obtiene un porcentaje de similitud.
    """

    if not registros_sheet:
        return {
            "registro": None,
            "similitud": 0,
            "estado": "Sin datos en Google Sheet",
        }

    nombre_normalizado = normalizar_nombre(nombre_carpeta)
    nombre_ordenado = normalizar_nombre_ordenado(nombre_carpeta)

    candidatos_ordenados = [
        registro["NombreOrdenadoGoogleSheet"]
        for registro in registros_sheet
    ]

    # Buscar por el nombre ordenado.
    resultado = process.extractOne(
        nombre_ordenado,
        candidatos_ordenados,
        scorer=fuzz.token_sort_ratio
    )

    if not resultado:
        return {
            "registro": None,
            "similitud": 0,
            "estado": "No encontrado",
        }

    _, similitud, indice = resultado
    mejor_registro = registros_sheet[indice]

    # Comparación exacta tras normalizar y ordenar palabras.
    if nombre_ordenado == mejor_registro["NombreOrdenadoGoogleSheet"]:
        estado = "Coincidencia exacta"

    elif similitud >= UMBRAL_COINCIDENCIA_PROBABLE:
        estado = "Coincidencia probable"

    elif similitud >= UMBRAL_REVISION_MANUAL:
        estado = "Posible coincidencia - revisar"

    else:
        estado = "No encontrado"

    return {
        "registro": mejor_registro,
        "similitud": round(similitud, 2),
        "estado": estado,
    }


# ============================================================
# LECTURA DE CARPETAS
# ============================================================

def contar_contenido_carpeta(carpeta: Path) -> tuple[int, int, int]:
    """
    Cuenta archivos, subcarpetas y total de elementos directos.
    """

    archivos = 0
    subcarpetas = 0

    try:
        for elemento in carpeta.iterdir():
            if elemento.is_file():
                archivos += 1
            elif elemento.is_dir():
                subcarpetas += 1

    except PermissionError:
        print(
            f"Advertencia: sin permisos para leer: {carpeta}",
            file=sys.stderr
        )

    total = archivos + subcarpetas

    return archivos, subcarpetas, total


def obtener_resultados(
    registros_sheet: list[dict]
) -> list[dict]:
    """
    Recorre las sedes y las carpetas hijas de personas.
    """

    resultado = []
    filas_sheet_incluidas = set()

    for sede in DIRECTORIO_PRINCIPAL.iterdir():

        if not sede.is_dir():
            continue

        if sede.name.startswith("."):
            continue

        for carpeta_persona in sede.iterdir():

            if not carpeta_persona.is_dir():
                continue

            nombre_original = carpeta_persona.name
            nombre_normalizado = normalizar_nombre(nombre_original)
            nombre_ordenado = normalizar_nombre_ordenado(nombre_original)

            archivos, subcarpetas, total_items = contar_contenido_carpeta(
                carpeta_persona
            )

            coincidencia = buscar_mejor_coincidencia(
                nombre_original,
                registros_sheet
            )

            registro_sheet = coincidencia["registro"]

            # Para evitar que un resultado muy débil quede asociado
            # incorrectamente a una persona, solo se muestran datos
            # de la hoja cuando el nivel amerita revisión o coincidencia.
            mostrar_datos_sheet = (
                coincidencia["similitud"] >= UMBRAL_REVISION_MANUAL
            )

            if registro_sheet and mostrar_datos_sheet:
                filas_sheet_incluidas.add(registro_sheet["FilaGoogleSheet"])

            resultado.append({
                "Sede": sede.name,
                "NombreOriginalCarpeta": nombre_original,
                "NombreNormalizadoCarpeta": nombre_normalizado,
                "NombreOrdenadoCarpeta": nombre_ordenado,
                "RutaCompleta": str(carpeta_persona),
                "EstaVacia": "Sí" if total_items == 0 else "No",
                "CantidadItems": total_items,
                "CantidadArchivos": archivos,
                "CantidadSubcarpetas": subcarpetas,

                "EstadoComparacion": coincidencia["estado"],
                "PorcentajeSimilitud": coincidencia["similitud"],

                "FilaGoogleSheet": (
                    registro_sheet["FilaGoogleSheet"]
                    if registro_sheet and mostrar_datos_sheet
                    else ""
                ),
                "FechaOriginalGoogleSheet": (
                    registro_sheet["FechaOriginalGoogleSheet"]
                    if registro_sheet and mostrar_datos_sheet
                    else ""
                ),
                "NombreEncontradoGoogleSheet": (
                    registro_sheet["NombreGoogleSheet"]
                    if registro_sheet and mostrar_datos_sheet
                    else ""
                ),
                "TieneMinutosInf": (
                    registro_sheet["TieneMinutosInf"]
                    if registro_sheet and mostrar_datos_sheet
                    else ""
                ),
                "ValorMinutosInf": (
                    registro_sheet["MinutosInf"]
                    if registro_sheet and mostrar_datos_sheet
                    else ""
                ),
            })

    for registro_sheet in registros_sheet:
        if registro_sheet["MinutosInfValido"]:
            continue

        if registro_sheet["FilaGoogleSheet"] in filas_sheet_incluidas:
            continue

        resultado.append({
            "Sede": "",
            "NombreOriginalCarpeta": "",
            "NombreNormalizadoCarpeta": "",
            "NombreOrdenadoCarpeta": "",
            "RutaCompleta": "",
            "EstaVacia": "",
            "CantidadItems": "",
            "CantidadArchivos": "",
            "CantidadSubcarpetas": "",

            "EstadoComparacion": "Sin carpeta coincidente",
            "PorcentajeSimilitud": "",

            "FilaGoogleSheet": registro_sheet["FilaGoogleSheet"],
            "FechaOriginalGoogleSheet": (
                registro_sheet["FechaOriginalGoogleSheet"]
            ),
            "NombreEncontradoGoogleSheet": registro_sheet["NombreGoogleSheet"],
            "TieneMinutosInf": registro_sheet["TieneMinutosInf"],
            "ValorMinutosInf": registro_sheet["MinutosInf"],
        })

    return resultado


# ============================================================
# EXPORTACIÓN
# ============================================================


def main():
    if not DIRECTORIO_PRINCIPAL.exists():
        raise FileNotFoundError(
            f"No existe el directorio: {DIRECTORIO_PRINCIPAL}"
        )

    if not ARCHIVO_CREDENCIALES.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ARCHIVO_CREDENCIALES}"
        )

    print("Leyendo registros de Google Sheets...")
    registros_sheet = obtener_datos_google_sheet()

    print(
        f"Registros válidos encontrados en Google Sheets: "
        f"{len(registros_sheet)}"
    )

    print("Analizando sedes y carpetas de personas...")
    datos = obtener_resultados(registros_sheet)

    exportar_excel(datos, ARCHIVO_SALIDA)

    coincidencias_exactas = sum(
        1
        for fila in datos
        if fila["EstadoComparacion"] == "Coincidencia exacta"
    )

    coincidencias_probables = sum(
        1
        for fila in datos
        if fila["EstadoComparacion"] == "Coincidencia probable"
    )

    por_revisar = sum(
        1
        for fila in datos
        if fila["EstadoComparacion"] == "Posible coincidencia - revisar"
    )

    no_encontrados = sum(
        1
        for fila in datos
        if fila["EstadoComparacion"] == "No encontrado"
    )

    sin_carpeta_coincidente = sum(
        1
        for fila in datos
        if fila["EstadoComparacion"] == "Sin carpeta coincidente"
    )

    carpetas_analizadas = sum(
        1
        for fila in datos
        if fila["RutaCompleta"]
    )

    print("\nProceso terminado.")
    print(f"Carpetas analizadas: {carpetas_analizadas}")
    print(f"Coincidencias exactas: {coincidencias_exactas}")
    print(f"Coincidencias probables: {coincidencias_probables}")
    print(f"Posibles coincidencias para revisar: {por_revisar}")
    print(f"No encontrados: {no_encontrados}")
    print(
        "Registros de Google Sheets sin carpeta coincidente: "
        f"{sin_carpeta_coincidente}"
    )
    print(f"\nExcel generado en:\n{ARCHIVO_SALIDA}")


if __name__ == "__main__":
    main()
