import re
from typing import Any


PATRON_ENTERO_POSITIVO = re.compile(r"[0-9]+")


def es_minutos_inf_valido(valor: Any) -> bool:
    """
    Indica si un valor representa una cantidad entera de minutos mayor que 0.

    Se aceptan tanto celdas numéricas como texto formado únicamente por
    dígitos. Los espacios exteriores se ignoran.
    """
    if valor is None or isinstance(valor, bool):
        return False

    texto = str(valor).strip()

    if not PATRON_ENTERO_POSITIVO.fullmatch(texto):
        return False

    return int(texto) > 0
