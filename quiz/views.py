from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from .models import Pregunta, UsuarioSesion, UsuarioRespuesta, PartidoRespuesta, PartidoPosicion
from .serializers import (
    PreguntaSerializer, UsuarioSesionSerializer, UsuarioRespuestaSerializer,
    MyTokenObtainPairSerializer, PartidoRespuestaSerializer, PartidoPosicionSerializer
)
from .utils import calcular_posicion, obtener_ranking_partidos
from core.models import Usuario, Partido
from rest_framework_simplejwt.views import TokenObtainPairView

class PreguntaViewSet(viewsets.ModelViewSet):
    serializer_class = PreguntaSerializer
    
    def get_queryset(self):
        queryset = Pregunta.objects.all()
        anio = self.request.query_params.get('anio')
        if anio:
            queryset = queryset.filter(eleccion__anio=anio)
        return queryset

class UsuarioSesionViewSet(viewsets.ModelViewSet):
    queryset = UsuarioSesion.objects.all()
    serializer_class = UsuarioSesionSerializer
    lookup_field = 'token' 

    def get_permissions(self):
    # Permitimos create, answers, finalizar, matches y retrieve (ver una sesión)
        if self.action in ['create', 'answers', 'finalizar_test', 'matches', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=['post'], url_path='answers')
    def answers(self, request):
        """
        PUNTO CLAVE: Recibe el array de respuestas de React.
        Payload: { "session_id": "token_o_id", "answers": [...] }
        """
        session_token = request.data.get('session_id')
        respuestas_data = request.data.get('answers', [])

        # Buscamos la sesión por token (que es lo que React suele tener)
        sesion = UsuarioSesion.objects.filter(token=session_token).first()
        if not sesion:
            return Response({"error": "Sesión no encontrada"}, status=404)

        try:
            with transaction.atomic():
                for item in respuestas_data:
                    UsuarioRespuesta.objects.update_or_create(
                        sesion=sesion,
                        pregunta_id=item['pregunta_id'],
                        defaults={'valor': item['valor']}
                    )
            return Response({"status": "respuestas_guardadas"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar_test(self, request, token=None):
        """
        Calcula resultados finales y marca la sesión como completada.
        """
        sesion = self.get_object()
        respuestas_queryset = sesion.respuestas.all()
        
        if not respuestas_queryset.exists():
            return Response({"error": "No hay respuestas para calcular"}, status=400)

        posX, posY = calcular_posicion(respuestas_queryset)
        
        sesion.resultado_x = posX
        sesion.resultado_y = posY
        sesion.completado = True
        sesion.save()

        ranking = obtener_ranking_partidos(posX, posY)

        return Response({
            "status": "finalizado",
            "token": sesion.token,
            "resultados": {"x": float(posX), "y": float(posY)},
            "ranking": ranking
        })
    
    # 1. Obtener afinidades (Ranking)
    @action(detail=True, methods=['get'], url_path='matches')
    def matches(self, request, token=None):
        sesion = self.get_object()
        
        if not sesion.completado:
            return Response({"error": "El quiz no ha sido finalizado"}, status=400)

        ranking = obtener_ranking_partidos(sesion.resultado_x, sesion.resultado_y)
        return Response(ranking)

    # 2. Vincular sesión anónima a un usuario
    @action(detail=False, methods=['post'], url_path='link-session')
    def link_session(self, request):
        token = request.data.get('session_id')
        usuario_id = request.data.get('usuario_id')
        
        sesion = UsuarioSesion.objects.filter(token=token).first()
        if sesion and not sesion.usuario:
            sesion.usuario_id = usuario_id
            sesion.save()
            return Response({"status": "vínculo exitoso"})
        
        return Response({"error": "No se pudo vincular"}, status=400)

class UsuarioRespuestaViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRespuesta.objects.all()
    serializer_class = UsuarioRespuestaSerializer
    permission_classes = [IsAdminUser]

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RespuestaPartidoViewSet(viewsets.ModelViewSet):
    queryset = PartidoRespuesta.objects.all()
    serializer_class = PartidoRespuestaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
class PartidoPosicionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartidoPosicion.objects.select_related('partido').all()
    serializer_class = PartidoPosicionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Nota: Si PartidoPosicion ya no tiene 'eleccion' directa, 
        # filtramos a través de las respuestas del partido si fuera necesario.
        return queryset

class MetricsDashboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        # Ajustado a 'completado=True' del nuevo modelo
        quizzes_completados = UsuarioSesion.objects.filter(completado=True).count()
        votantes_registrados = Usuario.objects.count()        
        partidos_analizados = Partido.objects.count()

        data = [
            {"value": f"{quizzes_completados:,}+", "label": "Quizzes completados"},
            {"value": f"{votantes_registrados:,}+", "label": "Votantes informados"},
            {"value": str(partidos_analizados), "label": "Partidos analizados"}
        ]
        return Response(data)
    
class ComparisonTableView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categorias = Pregunta.objects.values_list('categoria', flat=True).distinct()
        partidos = Partido.objects.all()[:3] 
        # En el nuevo modelo de Partido el campo es 'nombre'
        nombres_partidos = [p.nombre for p in partidos]

        rows = []
        for cat in categorias:
            if not cat: continue # Saltar categorías vacías
            row = {"topic": cat}
            for i, p in enumerate(partidos):
                letra = chr(97 + i)
                resp = PartidoRespuesta.objects.filter(
                    partido=p, 
                    pregunta__categoria=cat
                ).first()
                
                # Puedes mapear el valor (-2 a 2) a texto
                row[letra] = self._mapear_valor_a_texto(resp.valor) if resp else "Sin postura"
            rows.append(row)

        return Response({
            "headers": nombres_partidos,
            "rows": rows
        })

    def _mapear_valor_a_texto(self, valor):
        mapeo = {
            2: "Muy a favor",
            1: "A favor",
            0: "Neutral",
            -1: "En contra",
            -2: "Muy en contra"
        }
        return mapeo.get(valor, "Sin datos")
    
class PartidoPosicionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar las coordenadas calculadas de los partidos.
    Solo lectura, ya que el cálculo se realiza internamente.
    """
    queryset = PartidoPosicion.objects.all().select_related('partido')
    serializer_class = PartidoPosicionSerializer
    permission_classes = [AllowAny]