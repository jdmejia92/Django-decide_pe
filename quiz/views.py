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

    def create(self, request, *args, **kwargs):
        """
        Sobrescribimos el create para asegurarnos de que la respuesta 
        sea limpia y solo contenga lo que el serializer dice.
        """
        response = super().create(request, *args, **kwargs)
        return response

    @action(detail=True, methods=['post'])
    def finalizar_test(self, request, token=None):
        # 1. Obtenemos la sesión usando el token de la URL
        sesion = self.get_object()
        
        # 2. Recuperamos todas las respuestas asociadas a esta sesión
        respuestas_queryset = sesion.respuestas.all()
        
        if not respuestas_queryset.exists():
            return Response({"error": "No hay respuestas registradas para esta sesión"}, status=400)

        # 3. Calcular posición del usuario usando la lógica de utils.py
        posX, posY = calcular_posicion(respuestas_queryset)
        
        # 4. Guardar resultados en la base de datos y marcar como completado
        sesion.resultado_x = posX
        sesion.resultado_y = posY
        sesion.completado = True
        sesion.save()

        # 5. Obtener el ranking de compatibilidad con los partidos
        ranking = obtener_ranking_partidos(posX, posY)

        # 6. Devolver la respuesta final al frontend
        return Response({
            "status": "finalizado",
            "resultados": {
                "token": sesion.token,
                "x": float(posX),
                "y": float(posY)
            },
            "ranking": ranking
        })
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

class UsuarioRespuestaViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRespuesta.objects.all()
    serializer_class = UsuarioRespuestaSerializer
    permission_classes = [IsAdminUser]

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RespuestaPartidoViewSet(viewsets.ModelViewSet):
    queryset = PartidoRespuesta.objects.all()
    serializer_class = PartidoRespuestaSerializer
    permission_classes = [IsAdminUser]
    
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