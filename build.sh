#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear superusuario automáticamente usando variables de entorno
python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = 'admin@correo.com'

if not User.objects.filter(username=username).exists():
    if password:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'Superusuario "{username}" creado exitosamente.')
    else:
        print('Error: DJANGO_SUPERUSER_PASSWORD no está configurada.')
else:
    print(f'El superusuario "{username}" ya existe.')
END