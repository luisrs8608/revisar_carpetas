import unittest

from minutos import es_minutos_inf_valido


class EsMinutosInfValidoTests(unittest.TestCase):
    def test_acepta_enteros_positivos_y_texto_numerico(self):
        for valor in (1, 50, "1", "50", "001", " 50 "):
            with self.subTest(valor=valor):
                self.assertTrue(es_minutos_inf_valido(valor))

    def test_rechaza_valores_no_validos(self):
        for valor in (
            None,
            True,
            False,
            "",
            "   ",
            0,
            "0",
            "00",
            "abc",
            "-1",
            "+1",
            "1.5",
            "1,5",
            50.0,
            "50 min",
        ):
            with self.subTest(valor=valor):
                self.assertFalse(es_minutos_inf_valido(valor))


if __name__ == "__main__":
    unittest.main()
