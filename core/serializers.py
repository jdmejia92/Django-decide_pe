from rest_framework import serializers
from .models import Usuario, Partido, Eleccion

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'rol', 'first_name', 'last_name']
        # El rol solo se puede leer, no enviar al crear, para evitar 'auto-ascensos' a admin
        read_only_fields = ['rol']

    def create(self, validated_data):
        # Forzamos que el rol sea 'usuario' en el registro público
        validated_data['rol'] = 'usuario'
        # Creamos el usuario usando create_user para que encripte la password
        user = Usuario.objects.create_user(**validated_data)
        return user

class PartidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partido
        fields = ['id', 'nombre', 'sigla', 'nombre_largo']

class EleccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleccion
        fields = ['id', 'nombre', 'anio', 'actual']