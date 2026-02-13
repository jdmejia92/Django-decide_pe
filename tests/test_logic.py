from django.test import TestCase
from core.models import Eleccion, Partido
from quiz.models import Pregunta, UsuarioSesion, UsuarioRespuesta, PartidoPosicion
from quiz.utils import calcular_posicion, obtener_ranking_partidos

class LogicTest(TestCase):
    def setUp(self):
        self.eleccion = Eleccion.objects.create(nombre="Test", anio=2026)
        # Pregunta Económica (X) - Dirección Positiva
        self.p_econ = Pregunta.objects.create(
            eleccion=self.eleccion, eje='X', direccion=1, texto="Libre mercado", estado='activa'
        )
        # Pregunta Social (Y) - Dirección Negativa
        self.p_soc = Pregunta.objects.create(
            eleccion=self.eleccion, eje='Y', direccion=-1, texto="Conservadurismo", estado='activa'
        )

    def test_calculo_extremo_derecha_liberal(self):
        sesion = UsuarioSesion.objects.create()
        # A favor de libre mercado (2) y en contra de conservadurismo (-2)
        UsuarioRespuesta.objects.create(sesion=sesion, pregunta=self.p_econ, valor=2)
        UsuarioRespuesta.objects.create(sesion=sesion, pregunta=self.p_soc, valor=-2)

        posX, posY = calcular_posicion(sesion.respuestas.all())
        
        # (2 * 1 / 2) * 100 = 100
        # (-2 * -1 / 2) * 100 = 100
        self.assertEqual(posX, 100.0)
        self.assertEqual(posY, 100.0)