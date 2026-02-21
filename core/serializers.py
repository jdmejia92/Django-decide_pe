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
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'rol', 'nombre_completo']
        read_only_fields = ['rol']

    def validate_email(self, value):
        # Mantenemos tu validación de duplicados
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')

        if not validated_data.get('username'):
            email_part = validated_data['email'].split('@')[0]
            validated_data['username'] = email_part
            
        return Usuario.objects.create_user(password=password, **validated_data)


class EleccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleccion
        fields = ['id', 'nombre', 'anio', 'actual']

class PartidoMetadataImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidoMetadata
        fields = [
            'partido', 'candidato_presidencial', 'lider_partido', 
            'color_primario', 'plan_gobierno', 'candidato_key', 
            'anio_fundacion', 'tipo_organizacion'
        ]