from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser
from core.models import Eleccion, Partido
from quiz.models import Pregunta, PartidoRespuesta
from django.db import transaction
import io
import csv

# --- 1. VISTA DE ESTADÍSTICAS ---
class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        data = {
            "total_partidos": Partido.objects.count(),
            "total_preguntas": Pregunta.objects.count(),
            "elecciones": Eleccion.objects.values('nombre', 'anio', 'actual')
        }
        return Response(data)

# --- 2. Importar PARTIDOS (Catálogo) ---
class ImportarPartidosView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se envió el archivo"}, status=400)

        try:
            # Usamos utf-8-sig para manejar caracteres especiales como '¡' o tildes
            decoded_file = archivo.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            
            creados = 0
            actualizados = 0
            
            with transaction.atomic():
                for row in reader:
                    # El 'nombre' es nuestra llave para buscar
                    partido, created = Partido.objects.update_or_create(
                        nombre=row['nombre'],
                        defaults={
                            'nombre_largo': row.get('nombre_largo', ''),
                            'sigla': row.get('sigla', '')
                        }
                    )
                    if created:
                        creados += 1
                    else:
                        actualizados += 1
            
            return Response({
                "status": "Éxito", 
                "msg": f"Proceso completado. Creados: {creados}, Actualizados: {actualizados}"
            })
        except Exception as e:
            return Response({"error": f"Error en Partidos: {str(e)}"}, status=500)

# --- 3. importar RESPUESTAS DE PARTIDOS (Módulo Adicional) ---
from core.models import Eleccion # Asegúrate de importar el modelo Eleccion

class ImportarSoloRespuestasView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        # Obtenemos el año desde el cuerpo de la petición
        anio_eleccion = request.data.get('eleccion') 

        if not archivo: 
            return Response({"error": "Falta archivo"}, status=400)
        
        if not anio_eleccion:
            return Response({"error": "Debe especificar el año de la elección (ej: 2026)"}, status=400)

        try:
            # Buscamos la elección por año
            eleccion_obj = Eleccion.objects.filter(anio=anio_eleccion).first()
            if not eleccion_obj:
                return Response({"error": f"No existe una elección registrada para el año {anio_eleccion}"}, status=404)

            decoded_file = archivo.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            count = 0
            
            with transaction.atomic():
                for row in reader:
                    pregunta = Pregunta.objects.filter(id=row['pregunta']).first()
                    partido = Partido.objects.filter(id=row['partido']).first()
                    
                    if pregunta and partido:
                        # Ahora incluimos la elección tanto para buscar como para crear
                        PartidoRespuesta.objects.update_or_create(
                            pregunta=pregunta,
                            partido=partido,
                            eleccion=eleccion_obj, # <--- Relación agregada
                            defaults={
                                'valor': int(row['valor']),
                                'fuente': row.get('fuente', '')
                            }
                        )
                        count += 1
            
            return Response({"status": "Éxito", "msg": f"Se actualizaron {count} respuestas para la elección {anio_eleccion}."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# --- 4. Importar todo (Carga Masiva de Elección) ---
class ImportarTodoView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]
    def post(self, request):
        archivo = request.FILES.get('archivo')
        anio = request.data.get('anio')
        if not archivo or not anio: return Response({"error": "Faltan datos"}, status=400)
        try:
            decoded_file = archivo.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            eleccion = Eleccion.objects.get(anio=anio)
            with transaction.atomic():
                for row in reader:
                    pregunta, _ = Pregunta.objects.update_or_create(
                        texto=row['texto'], eleccion=eleccion,
                        defaults={'eje': row['eje'], 'direccion': int(row['direccion']), 'categoria': row['categoria']}
                    )
                    for key, value in row.items():
                        if key.startswith('valor_') and value:
                            sigla = key.replace('valor_', '')
                            partido = Partido.objects.filter(nombre__icontains=sigla).first()
                            if partido:
                                PartidoRespuesta.objects.update_or_create(
                                    pregunta=pregunta, partido=partido,
                                    defaults={'valor': int(value), 'fuente': row.get(f'fuente_{sigla}', '')}
                                )
            return Response({"status": "Éxito", "msg": "Carga masiva completa"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)