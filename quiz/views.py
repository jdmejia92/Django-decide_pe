from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import Pregunta, UsuarioSesion, UsuarioRespuesta, PartidoRespuesta, PartidoPosicion
from .serializers import PreguntaSerializer, UsuarioSesionSerializer, UsuarioRespuestaSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer, PartidoRespuestaSerializer, PartidoPosicionSerializer
from .utils import calcular_posicion, obtener_ranking_partidos

class PreguntaViewSet(viewsets.ModelViewSet):
    serializer_class = PreguntaSerializer
    
    def get_queryset(self):
        # Permite filtrar por año: /api/preguntas/?anio=2026
        queryset = Pregunta.objects.all()
        anio = self.request.query_params.get('anio')
        if anio:
            queryset = queryset.filter(eleccion__anio=anio)
        return queryset

class UsuarioSesionViewSet(viewsets.ModelViewSet):
    queryset = UsuarioSesion.objects.all()
    serializer_class = UsuarioSesionSerializer
    # Los usuarios anónimos deben poder crear una sesión para iniciar el test
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def finalizar_test(self, request, pk=None):
        sesion = self.get_object()
        respuestas_queryset = sesion.respuestas.all()
        
        if not respuestas_queryset.exists():
            return Response({"error": "No hay respuestas"}, status=400)

        # 1. Calcular posición del usuario
        posX, posY = calcular_posicion(respuestas_queryset)
        
        # 2. Guardar en BD
        sesion.resultado_x = posX
        sesion.resultado_y = posY
        sesion.estado = 'finalizada'
        sesion.save()

        # 3. Obtener el ranking de compatibilidad
        ranking = obtener_ranking_partidos(posX, posY)

        return Response({
            "status": "finalizado",
            "resultados": {
                "sesion_id": sesion.id,
                "x": posX,
                "y": posY
            },
            "ranking": ranking
        })

class UsuarioRespuestaViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRespuesta.objects.all()
    serializer_class = UsuarioRespuestaSerializer
    permission_classes = [AllowAny]

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RespuestaPartidoViewSet(viewsets.ModelViewSet):
    queryset = PartidoRespuesta.objects.all()
    serializer_class = PartidoRespuestaSerializer
    
    def get_permissions(self):
        # Cualquiera puede ver las respuestas de los partidos (GET)
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        # Solo admin puede crear, actualizar o borrar (POST, PUT, DELETE)
        return [IsAdminUser()]
    
class PartidoPosicionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de solo lectura para ver las coordenadas de los partidos en el mapa.
    """
    queryset = PartidoPosicion.objects.select_related('partido', 'eleccion').all()
    serializer_class = PartidoPosicionSerializer
    permission_classes = [AllowAny] # Cualquiera puede ver el mapa

    def get_queryset(self):
        queryset = super().get_queryset()
        anio = self.request.query_params.get('anio')
        if anio:
            queryset = queryset.filter(eleccion__anio=anio)
        return queryset