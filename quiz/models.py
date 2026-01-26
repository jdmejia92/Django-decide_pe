from django.db import models
from core.models import Partido, Usuario
import uuid
from .utils import calcular_posicion

class Pregunta(models.Model):
    eleccion = models.ForeignKey('core.Eleccion', on_delete=models.CASCADE, related_name='preguntas')

    id = models.AutoField(primary_key=True)
    texto = models.TextField()
    estado = models.CharField(max_length=20, default='activa')
    eje = models.CharField(max_length=1) # 'X' o 'Y'
    direccion = models.IntegerField() # 1 o -1
    categoria = models.CharField(max_length=50)

class PartidoRespuesta(models.Model):
    id = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    fuente = models.URLField(max_length=500, blank=True, null=True)
    eleccion = models.ForeignKey('core.Eleccion', on_delete=models.CASCADE)
    valor = models.IntegerField()

    def save(self, *args, **kwargs):
        # 1. Guardamos la respuesta primero
        super().save(*args, **kwargs)
        
        # 2. Obtenemos todas las respuestas de ESTE partido para ESTA elección
        respuestas_del_partido = PartidoRespuesta.objects.filter(
            partido=self.partido, 
            eleccion=self.eleccion
        )
        
        # 3. Calculamos la nueva posición usando tu lógica de utils
        nueva_posX, nueva_posY = calcular_posicion(respuestas_del_partido)
        
        # 4. Actualizamos o creamos el registro en PartidoPosicion
        # Importamos aquí para evitar importación circular
        from .models import PartidoPosicion
        
        PartidoPosicion.objects.update_or_create(
            partido=self.partido,
            eleccion=self.eleccion,
            defaults={
                'posicion_x': nueva_posX,
                'posicion_y': nueva_posY
            }
        )

class PartidoPosicion(models.Model):
    id = models.AutoField(primary_key=True)
    eleccion = models.ForeignKey('core.Eleccion', on_delete=models.CASCADE)
    
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    posicion_x = models.DecimalField(max_digits=5, decimal_places=2)
    posicion_y = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateTimeField(auto_now=True)

class UsuarioSesion(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    cod_sesion = models.CharField(max_length=20, unique=True, editable=False)
    estado = models.CharField(max_length=20, default='en_progreso')
    resultado_x = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    resultado_y = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    def save(self, *args, **kwargs):
        if not self.cod_sesion:
            # Generamos un código único de 8 caracteres (ej: A1B2C3D4)
            self.cod_sesion = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

class UsuarioRespuesta(models.Model):
    id = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    sesion = sesion = models.ForeignKey(
        'UsuarioSesion', 
        on_delete=models.CASCADE, 
        related_name='respuestas'
    )
    valor = models.IntegerField()