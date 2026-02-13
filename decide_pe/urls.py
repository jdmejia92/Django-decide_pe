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
from core.views import PartidoViewSet, EleccionViewSet, UsuarioViewSet, RegionViewSet
from quiz.views import PreguntaViewSet, UsuarioSesionViewSet, UsuarioRespuestaViewSet
from dashboard.views import AdminStatsView, ImportarPartidosView, ImportarSoloRespuestasView, ImportarPreguntasView, ImportarCandidatosView, ImportarMetadataView
from rest_framework_simplejwt.views import TokenRefreshView
from quiz.views import MyTokenObtainPairView, RespuestaPartidoViewSet, PartidoPosicionViewSet, MetricsDashboardView, ComparisonTableView

router = routers.DefaultRouter()
router.register(r'partidos', PartidoViewSet)
router.register(r'elecciones', EleccionViewSet)
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'quiz', UsuarioSesionViewSet, basename='quiz')
router.register(r'usuarios', UsuarioViewSet)
router.register(r'respuestas_usuario', UsuarioRespuestaViewSet)
router.register(r'respuestas-partidos', RespuestaPartidoViewSet)
router.register(r'partido-posiciones', PartidoPosicionViewSet, basename='partidoposicion')
router.register(r'regiones', RegionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Agrupamos todo bajo /api/ para que sea ordenado
    path('api/', include(router.urls)), 
    
    # Endpoints de Dashboard y Auth
    path('api/dashboard/stats/', AdminStatsView.as_view()),
    path('api/dashboard/importar-partidos/', ImportarPartidosView.as_view()),
    path('api/dashboard/importar-respuestas/', ImportarSoloRespuestasView.as_view()),
    path('api/dashboard/importar-preguntas/', ImportarPreguntasView.as_view()),
    path('api/dashboard/importar-candidatos/', ImportarCandidatosView.as_view()),
    path('api/dashboard/importar-metadata/', ImportarMetadataView.as_view(), name='importar-metadata'),
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/metrics/', MetricsDashboardView.as_view(), name='metrics'),
    path('api/comparison/', ComparisonTableView.as_view(), name='comparison-table'),
]