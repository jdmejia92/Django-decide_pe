from rest_framework import serializers
from .models import Usuario, Partido, PartidoMetadata, Candidato, Region, Eleccion
from django.contrib.auth.password_validation import validate_password

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'nombre']

class CandidatoSerializer(serializers.ModelSerializer):
    # Usamos region_rel que es como lo llamaste en tu modelo
    nombre_region = serializers.ReadOnlyField(source='region_rel.nombre')

    class Meta:
        model = Candidato
        fields = [
            'id', 
            'nombres', 
            'apellidos', 
            'cargo', 
            'numero', 
            'region_rel', 
            'nombre_region',
            'foto',
            'hojavida'
        ]

class PartidoSerializer(serializers.ModelSerializer):
    # Traemos los datos de la tabla PartidoMetadata hacia el JSON de Partido
    candidato_presidencial = serializers.ReadOnlyField(source='metadata.candidato_presidencial')
    color_primario = serializers.ReadOnlyField(source='metadata.color_primario')
    logo_key = serializers.ReadOnlyField(source='metadata.logo_key')

    class Meta:
        model = Partido
        fields = [
            'id', 
            'nombre', 
            'nombre_largo', 
            'sigla', 
            'candidato_presidencial', 
            'color_primario', 
            'logo_key'
        ]

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    # Hacemos el email explícitamente requerido
    email = serializers.EmailField(required=True)

    class Meta:
        model = Usuario
        # Mantenemos username por compatibilidad interna de Django, 
        # pero el foco principal es el email.
        fields = ['id', 'username', 'email', 'password', 'rol', 'nombre_completo']
        read_only_fields = ['rol']

    def validate_email(self, value):
        # Validamos que el email no esté duplicado
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Si tu frontend no envía un 'username', usamos la primera parte del email
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email'].split('@')[0]
            
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EleccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleccion
        fields = ['id', 'nombre', 'anio', 'actual']

class PartidoMetadataImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidoMetadata
        fields = [
            'partido', 'candidato_presidencial', 'lider_partido', 
            'color_primario', 'logo_key', 'candidato_key', 
            'anio_fundacion', 'tipo_organizacion'
        ]