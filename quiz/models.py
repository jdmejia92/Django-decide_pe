from django.db import models
from core.models import Partido, Usuario, Eleccion
import uuid

class Pregunta(models.Model):
    EJES = (('X', 'Económico'), ('Y', 'Social'))
    ESTADOS = (('activa', 'Activa'), ('inactiva', 'Inactiva'))

    eleccion = models.ForeignKey(Eleccion, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField()
    eje = models.CharField(max_length=1, choices=EJES) # SQL: enum('X','Y')
    direccion = models.IntegerField() # SQL: tinyint(4) (+1 o -1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    categoria = models.CharField(max_length=50, blank=True, null=True)

class PartidoRespuesta(models.Model):
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    valor = models.IntegerField() # SQL: tinyint(4) (-2 a +2)
    fuente = models.CharField(max_length=500, blank=True, null=True)

class PartidoPosicion(models.Model):
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    posicion_x = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    posicion_y = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        # Esto asegura que use el nombre de tabla que tienes en tu SQL
        db_table = 'partidoposicioncache'

class UsuarioSesion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=10, unique=True, editable=False) # SQL: token varchar(10)
    resultado_x = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    resultado_y = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    completado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

class UsuarioRespuesta(models.Model):
    sesion = models.ForeignKey(UsuarioSesion, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    valor = models.IntegerField() # SQL: tinyint(4)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)