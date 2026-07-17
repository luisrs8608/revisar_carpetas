import tempfile
import unittest
from pathlib import Path

from borrar_carpetas_con_minutos import (
    CarpetaLocal,
    CoincidenciaCarpeta,
    confirmar_borrado,
    mover_carpetas_a_papelera,
    ruta_es_segura,
    seleccionar_carpetas,
)


def crear_registro(fila, nombre, minutos):
    nombre_ordenado = " ".join(sorted(nombre.lower().split()))
    return {
        "FilaGoogleSheet": fila,
        "NombreGoogleSheet": nombre,
        "NombreOrdenadoGoogleSheet": nombre_ordenado,
        "MinutosInf": minutos,
    }


def crear_carpeta(ruta, nombre):
    return CarpetaLocal(
        sede=ruta.parent.name,
        nombre=nombre,
        nombre_ordenado=" ".join(sorted(nombre.lower().split())),
        ruta=ruta,
    )


class SeleccionarCarpetasTests(unittest.TestCase):
    def test_selecciona_coincidencias_exactas_y_probables(self):
        registros = [
            crear_registro(12, "Ana Perez", "30"),
            crear_registro(13, "Juan Perez", "45"),
            crear_registro(14, "Nombre Distinto", "20"),
            crear_registro(15, "Sin Minutos", "x"),
        ]
        carpetas = [
            crear_carpeta(Path("/sedes/centro/Ana_Perez"), "Ana Perez"),
            crear_carpeta(Path("/sedes/norte/Juan_Peres"), "Juan Peres"),
        ]

        resultado = seleccionar_carpetas(registros, carpetas, 90)

        self.assertEqual(
            [item.fila_google_sheet for item in resultado.elegibles],
            [12, 13],
        )
        self.assertEqual(resultado.elegibles[0].estado, "Coincidencia exacta")
        self.assertEqual(
            resultado.elegibles[1].estado,
            "Coincidencia probable",
        )
        self.assertEqual(
            [item["FilaGoogleSheet"] for item in resultado.filas_sin_carpeta],
            [14],
        )

    def test_omite_una_fila_con_varias_carpetas(self):
        registros = [crear_registro(12, "Ana Perez", "30")]
        carpetas = [
            crear_carpeta(Path("/sedes/centro/Ana_Perez"), "Ana Perez"),
            crear_carpeta(Path("/sedes/norte/Ana-Perez"), "Ana Perez"),
        ]

        resultado = seleccionar_carpetas(registros, carpetas, 90)

        self.assertEqual(resultado.elegibles, [])
        self.assertEqual(len(resultado.ambiguas), 2)

    def test_omite_una_carpeta_asociada_a_varias_filas(self):
        registros = [
            crear_registro(12, "Ana Perez", "30"),
            crear_registro(13, "Ana Perez", "40"),
        ]
        carpetas = [
            crear_carpeta(Path("/sedes/centro/Ana_Perez"), "Ana Perez")
        ]

        resultado = seleccionar_carpetas(registros, carpetas, 90)

        self.assertEqual(resultado.elegibles, [])
        self.assertEqual(len(resultado.ambiguas), 2)


class SeguridadBorradoTests(unittest.TestCase):
    def test_confirmacion_exige_la_palabra_exacta(self):
        self.assertTrue(confirmar_borrado(2, lambda _: "BORRAR"))
        self.assertFalse(confirmar_borrado(2, lambda _: "borrar"))
        self.assertFalse(confirmar_borrado(0, lambda _: "BORRAR"))

    def test_solo_acepta_carpetas_en_el_segundo_nivel(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            sede = raiz / "sede"
            persona = sede / "persona"
            nivel_extra = persona / "estudio"
            sede.mkdir()
            persona.mkdir()
            nivel_extra.mkdir()

            self.assertTrue(ruta_es_segura(persona, raiz))
            self.assertFalse(ruta_es_segura(sede, raiz))
            self.assertFalse(ruta_es_segura(nivel_extra, raiz))
            self.assertFalse(ruta_es_segura(raiz / "inexistente", raiz))

    def test_mueve_solo_rutas_seguras_mediante_la_funcion_recibida(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            persona = raiz / "sede" / "persona"
            persona.mkdir(parents=True)
            carpeta = crear_carpeta(persona, "persona")
            coincidencia = CoincidenciaCarpeta(
                fila_google_sheet=12,
                nombre_google_sheet="persona",
                minutos_inf="20",
                carpeta=carpeta,
                similitud=100,
                estado="Coincidencia exacta",
            )
            rutas_recibidas = []

            movidas, fallidas = mover_carpetas_a_papelera(
                [coincidencia],
                raiz,
                rutas_recibidas.append,
            )

            self.assertEqual((movidas, fallidas), (1, 0))
            self.assertEqual(rutas_recibidas, [persona])


if __name__ == "__main__":
    unittest.main()
