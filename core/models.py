from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, default='usuario')

    def save(self, *args, **kwargs):
        # Lógica automática: si es admin por rol, darle acceso al staff
        if self.rol == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class Partido(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    sigla = models.CharField(max_length=20)
    nombre_largo = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nombre, self.sigla, self.nombre_largo
    
class Eleccion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    anio = models.IntegerField(unique=True)
    actual = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} ({self.anio})"