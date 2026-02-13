from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from .models import Usuario, Partido, Eleccion
from .serializers import UsuarioSerializer, PartidoSerializer, EleccionSerializer

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
    permission_classes = [IsAuthenticatedOrReadOnly]

class EleccionViewSet(viewsets.ModelViewSet):
    queryset = Eleccion.objects.all()
    serializer_class = EleccionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]