from rest_framework import serializers
from .models import Pregunta, PartidoRespuesta, UsuarioSesion, UsuarioRespuesta, PartidoPosicion
from core.serializers import EleccionSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class PreguntaSerializer(serializers.ModelSerializer):
    # Anidamos la elección para que el frontend sepa a qué año pertenece la pregunta
    eleccion_info = EleccionSerializer(source='eleccion', read_only=True)

    class Meta:
        model = Pregunta
        fields = ['id', 'eleccion', 'eleccion_info', 'texto', 'estado', 'eje', 'direccion', 'categoria']

class PartidoRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidoRespuesta
        fields = ['id', 'partido', 'pregunta', 'eleccion', 'valor']

class UsuarioRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRespuesta
        fields = ['pregunta', 'sesion', 'valor']

class UsuarioSesionSerializer(serializers.ModelSerializer):
    # Incluimos las respuestas para que el admin pueda ver qué contestó el usuario
    respuestas = UsuarioRespuestaSerializer(many=True, read_only=True, source='usuariorespuesta_set')

    class Meta:
        model = UsuarioSesion
        fields = [
            'id', 
            'cod_sesion', 
            'usuario',
            'resultado_x', 
            'resultado_y', 
            'estado',
            'respuestas'
        ]
        read_only_fields = ['cod_sesion', 'resultado_x', 'resultado_y', 'estado', 'respuestas']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['rol'] = user.rol
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'rol': self.user.rol,
            'first_name': self.user.first_name,
            'full_name': f"{self.user.first_name} {self.user.last_name}".strip()
        }
        return data
    
class PartidoPosicionSerializer(serializers.ModelSerializer):
    # Traemos campos del partido relacionado para facilitar el trabajo al frontend
    nombre_partido = serializers.ReadOnlyField(source='partido.nombre')
    sigla_partido = serializers.ReadOnlyField(source='partido.sigla')
    anio_eleccion = serializers.ReadOnlyField(source='eleccion.anio')

    class Meta:
        model = PartidoPosicion
        fields = [
            'id', 
            'partido', 
            'nombre_partido', 
            'sigla_partido', 
            'eleccion', 
            'anio_eleccion', 
            'posicion_x', 
            'posicion_y', 
            'fecha'
        ]