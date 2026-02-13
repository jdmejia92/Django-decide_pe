from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .models import Usuario, Partido, Eleccion, Region
from .serializers import UsuarioSerializer, PartidoSerializer, EleccionSerializer, CandidatoSerializer, RegionSerializer
from quiz.models import PartidoRespuesta
from quiz.serializers import PartidoRespuestaSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        # Si la acción es 'create' (POST /api/usuarios/), permitimos a cualquiera
        if self.action == 'create':
            return [AllowAny()]
        # Para cualquier otra acción (list, retrieve, update, delete), solo admin
        return [IsAdminUser()]

class PartidoViewSet(viewsets.ModelViewSet):
    queryset = Partido.objects.all()
    serializer_class = PartidoSerializer
    permission_classes = [AllowAny]

    # Esta es la acción que estaba causando el error por falta de import
    @action(detail=False, url_path='sigla/(?P<sigla>[^/.]+)')
    def por_sigla(self, request, sigla=None):
        # iexact sirve para que no importe si es mayúscula o minúscula
        partido = get_object_or_404(Partido, sigla__iexact=sigla)
        serializer = self.get_serializer(partido)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def candidatos(self, request, pk=None):
        partido = self.get_object()
        # Asegúrate de que el 'related_name' en tu modelo sea 'candidatos'
        candidatos = partido.candidatos.all() 
        serializer = CandidatoSerializer(candidatos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def respuestas(self, request, pk=None):
        # Filtramos las respuestas del partido
        respuestas = PartidoRespuesta.objects.filter(partido_id=pk)
        
        # Diccionario para convertir el "valor" numérico en texto legible
        mapa_posiciones = {
            2: "Muy a favor",
            1: "A favor",
            0: "Neutro / No precisa",
            -1: "En contra",
            -2: "Muy en contra"
        }
        
        data = []
        for r in respuestas:
            data.append({
                "id": r.id,
                "partido": r.partido_id,
                "pregunta": r.pregunta_id, 
                "posicion": mapa_posiciones.get(r.valor, "Sin datos"), # Convertimos el tinyint a texto
                "explicacion": r.fuente, # Usamos fuente como explicación ya que no tienes campo explicación
                "fuente": r.fuente
            })
        return Response(data)

class EleccionViewSet(viewsets.ModelViewSet):
    queryset = Eleccion.objects.all()
    serializer_class = EleccionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, list):
            resultados = []
            for item in data:
                # Busca por nombre, si no existe lo crea
                obj, created = Region.objects.get_or_create(nombre=item['nombre'])
                resultados.append(RegionSerializer(obj).data)
            return Response(resultados, status=status.HTTP_201_CREATED)
        
        return super().create(request, *args, **kwargs)