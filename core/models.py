from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)
    
class Usuario(AbstractUser):
    ROLES = (
        ('user', 'Usuario'),
        ('admin', 'Administrador'),
    )
    # db_column='rol' para asegurar que coincida con tu SQL
    rol = models.CharField(max_length=20, choices=ROLES, default='user', db_column='rol')
    nombre_completo = models.CharField(max_length=100, db_column='nombre', blank=True, null=True)
    objects = CustomUserManager()

class Region(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Partido(models.Model):
    nombre = models.CharField(max_length=50)
    nombre_largo = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.nombre
    
class PartidoMetadata(models.Model):
    partido = models.OneToOneField(Partido, on_delete=models.CASCADE, related_name='metadata')
    candidato_presidencial = models.CharField(max_length=100, blank=True, null=True)
    lider_partido = models.CharField(max_length=100, blank=True, null=True)
    color_primario = models.CharField(max_length=7, default='#000000')
    logo_key = models.CharField(max_length=50)
    candidato_key = models.CharField(max_length=50, default='DEFAULT_CANDIDATE')
    anio_fundacion = models.IntegerField(blank=True, null=True) # SQL utiliza tipo YEAR
    tipo_organizacion = models.CharField(max_length=50, default='Partido Político')

class Candidato(models.Model):
    # Basado en la tabla 'candidato' del SQL
    CARGOS = (
        ('presidente', 'Presidente'),
        ('1er vicepresidente', '1er Vicepresidente'),
        ('2do vicepresidente', '2do Vicepresidente'),
        ('diputado', 'Diputado'),
        ('senador nacional', 'Senador Nacional'),
        ('senador regional', 'Senador Regional'),
        ('parlamento andino', 'Parlamento Andino'),
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50, choices=CARGOS)
    numero = models.IntegerField(null=True, blank=True)
    region_rel = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, db_column='id_region')
    region_texto = models.CharField(max_length=100, null=True, blank=True)
    foto = models.URLField(max_length=500, null=True, blank=True)
    hojavida = models.URLField(max_length=500, null=True, blank=True)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='candidatos')

class Eleccion(models.Model):
    nombre = models.CharField(max_length=100)
    anio = models.IntegerField(unique=True)
    actual = models.BooleanField(default=False)