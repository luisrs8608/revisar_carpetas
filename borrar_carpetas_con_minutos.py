import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rapidfuzz import fuzz

from minutos import es_minutos_inf_valido


@dataclass(frozen=True)
class CarpetaLocal:
    sede: str
    nombre: str
    nombre_ordenado: str
    ruta: Path


@dataclass(frozen=True)
class CoincidenciaCarpeta:
    fila_google_sheet: int
    nombre_google_sheet: str
    minutos_inf: str
    carpeta: CarpetaLocal
    similitud: float
    estado: str


@dataclass(frozen=True)
class ResultadoSeleccion:
    elegibles: list[CoincidenciaCarpeta]
    ambiguas: list[CoincidenciaCarpeta]
    filas_sin_carpeta: list[dict]


def listar_carpetas_locales(
    directorio_principal: Path,
    normalizar_nombre_ordenado: Callable[[str], str],
) -> list[CarpetaLocal]:
    """Lista carpetas de personas directas dentro de cada sede."""
    carpetas = []

    for sede in sorted(
        directorio_principal.iterdir(),
        key=lambda ruta: ruta.name.casefold(),
    ):
        if (
            not sede.is_dir()
            or sede.is_symlink()
            or sede.name.startswith(".")
        ):
            continue

        for carpeta in sorted(
            sede.iterdir(),
            key=lambda ruta: ruta.name.casefold(),
        ):
            if (
                not carpeta.is_dir()
                or carpeta.is_symlink()
                or carpeta.name.startswith(".")
            ):
                continue

            carpetas.append(CarpetaLocal(
                sede=sede.name,
                nombre=carpeta.name,
                nombre_ordenado=normalizar_nombre_ordenado(carpeta.name),
                ruta=carpeta,
            ))

    return carpetas


def seleccionar_carpetas(
    registros_sheet: list[dict],
    carpetas: list[CarpetaLocal],
    umbral_probable: int,
) -> ResultadoSeleccion:
    """
    Selecciona solamente relaciones unívocas exactas o probables.

    Una relación se considera ambigua si una fila tiene más de una carpeta
    candidata o si una carpeta es candidata para más de una fila.
    """
    registros_con_minutos = [
        registro
        for registro in registros_sheet
        if es_minutos_inf_valido(registro.get("MinutosInf"))
    ]

    candidatos_por_fila = defaultdict(list)
    filas_por_carpeta = defaultdict(set)

    for registro in registros_con_minutos:
        fila_sheet = int(registro["FilaGoogleSheet"])
        nombre_sheet = registro["NombreOrdenadoGoogleSheet"]

        for carpeta in carpetas:
            similitud = float(fuzz.token_sort_ratio(
                nombre_sheet,
                carpeta.nombre_ordenado,
            ))
            es_exacta = nombre_sheet == carpeta.nombre_ordenado

            if not es_exacta and similitud < umbral_probable:
                continue

            coincidencia = CoincidenciaCarpeta(
                fila_google_sheet=fila_sheet,
                nombre_google_sheet=registro["NombreGoogleSheet"],
                minutos_inf=str(registro["MinutosInf"]),
                carpeta=carpeta,
                similitud=round(similitud, 2),
                estado=(
                    "Coincidencia exacta"
                    if es_exacta
                    else "Coincidencia probable"
                ),
            )
            candidatos_por_fila[fila_sheet].append(coincidencia)
            filas_por_carpeta[carpeta.ruta].add(fila_sheet)

    elegibles = []
    ambiguas = []
    filas_sin_carpeta = []

    for registro in registros_con_minutos:
        fila_sheet = int(registro["FilaGoogleSheet"])
        candidatos = candidatos_por_fila[fila_sheet]

        if not candidatos:
            filas_sin_carpeta.append(registro)
            continue

        fila_ambigua = len(candidatos) != 1

        for coincidencia in candidatos:
            carpeta_ambigua = (
                len(filas_por_carpeta[coincidencia.carpeta.ruta]) != 1
            )

            if fila_ambigua or carpeta_ambigua:
                ambiguas.append(coincidencia)
            else:
                elegibles.append(coincidencia)

    elegibles.sort(key=lambda item: item.fila_google_sheet)
    ambiguas.sort(key=lambda item: (
        item.fila_google_sheet,
        str(item.carpeta.ruta).casefold(),
    ))
    filas_sin_carpeta.sort(key=lambda item: int(item["FilaGoogleSheet"]))

    return ResultadoSeleccion(
        elegibles=elegibles,
        ambiguas=ambiguas,
        filas_sin_carpeta=filas_sin_carpeta,
    )


def mostrar_vista_previa(resultado: ResultadoSeleccion) -> None:
    print("\nCarpetas que se moverán a la Papelera:")

    if not resultado.elegibles:
        print("  Ninguna.")

    for coincidencia in resultado.elegibles:
        print(
            f"  Fila {coincidencia.fila_google_sheet} | "
            f"{coincidencia.nombre_google_sheet} | "
            f"minutos: {coincidencia.minutos_inf} | "
            f"{coincidencia.estado} ({coincidencia.similitud}%)\n"
            f"    {coincidencia.carpeta.ruta}"
        )

    if resultado.ambiguas:
        print("\nCoincidencias ambiguas omitidas:")
        for coincidencia in resultado.ambiguas:
            print(
                f"  Fila {coincidencia.fila_google_sheet} | "
                f"{coincidencia.nombre_google_sheet} -> "
                f"{coincidencia.carpeta.ruta} "
                f"({coincidencia.similitud}%)"
            )

    if resultado.filas_sin_carpeta:
        print("\nFilas con minutos sin carpeta coincidente:")
        for registro in resultado.filas_sin_carpeta:
            print(
                f"  Fila {registro['FilaGoogleSheet']} | "
                f"{registro['NombreGoogleSheet']} | "
                f"minutos: {registro['MinutosInf']}"
            )

    print(
        "\nResumen: "
        f"{len(resultado.elegibles)} para Papelera, "
        f"{len(resultado.ambiguas)} relaciones ambiguas, "
        f"{len(resultado.filas_sin_carpeta)} sin carpeta."
    )


def confirmar_borrado(
    cantidad: int,
    leer: Callable[[str], str] = input,
) -> bool:
    if cantidad == 0:
        return False

    try:
        respuesta = leer(
            f"\nPara mover {cantidad} carpeta(s) a la Papelera, "
            "escribe BORRAR: "
        )
    except (EOFError, KeyboardInterrupt):
        print("\nOperación cancelada.")
        return False

    return respuesta.strip() == "BORRAR"


def ruta_es_segura(ruta: Path, directorio_principal: Path) -> bool:
    """Valida que la ruta sea una carpeta directa dentro de una sede."""
    if ruta.is_symlink() or not ruta.exists() or not ruta.is_dir():
        return False

    try:
        raiz_resuelta = directorio_principal.resolve(strict=True)
        ruta_resuelta = ruta.resolve(strict=True)
        relativa = ruta_resuelta.relative_to(raiz_resuelta)
    except (FileNotFoundError, OSError, ValueError):
        return False

    return len(relativa.parts) == 2


def enviar_a_papelera(ruta: Path) -> None:
    try:
        from send2trash import send2trash
    except ImportError as error:
        raise RuntimeError(
            "No está instalada la dependencia Send2Trash. "
            "Ejecuta: pip install -r requirements.txt"
        ) from error

    send2trash(str(ruta))


def mover_carpetas_a_papelera(
    coincidencias: list[CoincidenciaCarpeta],
    directorio_principal: Path,
    mover: Callable[[Path], None] = enviar_a_papelera,
) -> tuple[int, int]:
    movidas = 0
    fallidas = 0

    for coincidencia in coincidencias:
        ruta = coincidencia.carpeta.ruta

        if not ruta_es_segura(ruta, directorio_principal):
            print(f"Omitida por seguridad: {ruta}", file=sys.stderr)
            fallidas += 1
            continue

        try:
            mover(ruta)
            print(f"Movida a la Papelera: {ruta}")
            movidas += 1
        except Exception as error:
            print(f"No se pudo mover {ruta}: {error}", file=sys.stderr)
            fallidas += 1

    return movidas, fallidas


def main() -> None:
    # La importación carga config.json igual que el comparador principal.
    import revisar_carpetas as comparador

    if not comparador.DIRECTORIO_PRINCIPAL.exists():
        raise FileNotFoundError(
            f"No existe el directorio: {comparador.DIRECTORIO_PRINCIPAL}"
        )

    if not comparador.ARCHIVO_CREDENCIALES.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {comparador.ARCHIVO_CREDENCIALES}"
        )

    print("Leyendo registros de Google Sheets...")
    registros = comparador.obtener_datos_google_sheet()

    print("Buscando carpetas locales...")
    carpetas = listar_carpetas_locales(
        comparador.DIRECTORIO_PRINCIPAL,
        comparador.normalizar_nombre_ordenado,
    )

    resultado = seleccionar_carpetas(
        registros,
        carpetas,
        comparador.UMBRAL_COINCIDENCIA_PROBABLE,
    )
    mostrar_vista_previa(resultado)

    if not resultado.elegibles:
        print("\nNo hay carpetas elegibles. No se realizaron cambios.")
        return

    if not confirmar_borrado(len(resultado.elegibles)):
        print("\nConfirmación incorrecta. No se realizaron cambios.")
        return

    movidas, fallidas = mover_carpetas_a_papelera(
        resultado.elegibles,
        comparador.DIRECTORIO_PRINCIPAL,
    )

    print(
        f"\nProceso terminado: {movidas} carpeta(s) movida(s) "
        f"y {fallidas} omitida(s) o fallida(s)."
    )


if __name__ == "__main__":
    main()
