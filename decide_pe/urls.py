"""
URL configuration for decide_pe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from core.views import PartidoViewSet, EleccionViewSet, UsuarioViewSet
from quiz.views import PreguntaViewSet, UsuarioSesionViewSet, UsuarioRespuestaViewSet
from dashboard.views import AdminStatsView, ImportarPartidosView, ImportarSoloRespuestasView, ImportarTodoView
from rest_framework_simplejwt.views import TokenRefreshView
from quiz.views import MyTokenObtainPairView, RespuestaPartidoViewSet, PartidoPosicionViewSet

router = routers.DefaultRouter()
router.register(r'partidos', PartidoViewSet)
router.register(r'elecciones', EleccionViewSet)
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'sesiones', UsuarioSesionViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'respuestas_usuario', UsuarioRespuestaViewSet)
router.register(r'respuestas-partidos', RespuestaPartidoViewSet)
router.register(r'partido-posiciones', PartidoPosicionViewSet, basename='partidoposicion')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # Todas las rutas automáticas
    path('api/dashboard/stats/', AdminStatsView.as_view()),
    path('api/dashboard/importar-partidos/', ImportarPartidosView.as_view()),
    path('api/dashboard/importar-respuestas/', ImportarSoloRespuestasView.as_view()),
    path('api/dashboard/importar-todo/', ImportarTodoView.as_view()),
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
