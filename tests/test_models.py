from django.test import TestCase
from quiz.models import UsuarioSesion
from core.models import Usuario

class ModelsTest(TestCase):
    def test_generacion_token_sesion(self):
        sesion = UsuarioSesion.objects.create()
        self.assertIsNotNone(sesion.token)
        self.assertEqual(len(sesion.token), 10)

    def test_rol_admin_is_staff(self):
        user = Usuario.objects.create(username="admin_test", rol="admin")
        self.assertTrue(user.is_staff)