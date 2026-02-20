from rest_framework import serializers
from .models import Pregunta, PartidoRespuesta, UsuarioSesion, UsuarioRespuesta, PartidoPosicion
from core.serializers import EleccionSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class PreguntaSerializer(serializers.ModelSerializer):
    eleccion_info = EleccionSerializer(source='eleccion', read_only=True)

    class Meta:
        model = Pregunta
        fields = ['id', 'eleccion', 'eleccion_info', 'texto', 'estado', 'eje', 'direccion', 'categoria']

class PartidoRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidoRespuesta
        fields = ['id', 'partido', 'pregunta', 'valor', 'fuente']

class UsuarioRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRespuesta
        fields = ['pregunta', 'valor'] # No incluimos sesion aquí porque se suele enviar en el contexto

class UsuarioSesionSerializer(serializers.ModelSerializer):
    usuario_id = serializers.PrimaryKeyRelatedField(
        source='usuario', 
        read_only=True, 
        allow_null=True
    )
    
    respuestas = UsuarioRespuestaSerializer(many=True, read_only=True)

    class Meta:
        model = UsuarioSesion
        fields = [ 
            'token', 
            'usuario_id',
            'eleccion_id',
            'resultado_x',
            'resultado_y', 
            'completado',
            'fecha',
            'respuestas'
        ]
        # 'eleccion' debe estar aquí para que el POST de React no falle al no enviarlo
        read_only_fields = ['token', 'resultado_x', 'resultado_y', 'fecha', 'respuestas', 'eleccion_id']

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
            'full_name': self.user.nombre_completo # Usamos el campo del SQL
        }
        return data

class PartidoPosicionSerializer(serializers.ModelSerializer):
    nombre_partido = serializers.ReadOnlyField(source='partido.nombre')
    sigla_partido = serializers.ReadOnlyField(source='partido.sigla')

    class Meta:
        model = PartidoPosicion
        fields = ['id', 'partido', 'nombre_partido', 'sigla_partido', 'posicion_x', 'posicion_y', 'fecha_calculo']

class PartidoPosicionSerializer(serializers.ModelSerializer):
    # Traemos datos del partido para que el frontend sepa de quién es cada punto
    nombre_partido = serializers.ReadOnlyField(source='partido.nombre')
    sigla_partido = serializers.ReadOnlyField(source='partido.sigla')

    class Meta:
        model = PartidoPosicion
        fields = [
            'id', 
            'partido', 
            'nombre_partido', 
            'sigla_partido', 
            'posicion_x', 
            'posicion_y', 
            'fecha_calculo'
        ]