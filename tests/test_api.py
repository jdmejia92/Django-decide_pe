from rest_framework.test import APITestCase
from rest_framework import status
from quiz.models import UsuarioSesion, Pregunta
from core.models import Eleccion

class ApiTest(APITestCase):
    def setUp(self):
        self.eleccion = Eleccion.objects.create(nombre="Test", anio=2026)
        self.pregunta = Pregunta.objects.create(
                        eleccion=self.eleccion, 
                        eje='X', 
                        direccion=1, 
                        texto="Test", 
                        estado='activa',
                        categoria="General"  # <--- Añade esto
                    )
        self.sesion = UsuarioSesion.objects.create()

    def test_finalizar_test_endpoint(self):
        # Primero guardamos una respuesta via API o DB
        self.sesion.respuestas.create(pregunta=self.pregunta, valor=2)
        
        url = f'/api/sesiones/{self.sesion.token}/finalizar_test/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['resultados']['x'] > 0)
        self.assertEqual(response.data['status'], 'finalizado')