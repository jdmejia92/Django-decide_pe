from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser
from core.models import Eleccion, Partido
from quiz.models import Pregunta, PartidoRespuesta, PartidoPosicion
from django.db import transaction
from quiz.utils import calcular_posicion
import io
import csv

class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        data = {
            "total_partidos": Partido.objects.count(),
            "total_preguntas": Pregunta.objects.count(),
            "elecciones": Eleccion.objects.values('nombre', 'anio', 'actual')
        }
        return Response(data)

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

from core.models import Eleccion

class ImportarSoloRespuestasView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        anio_eleccion = request.data.get('eleccion') 

        if not archivo or not anio_eleccion: 
            return Response({"error": "Faltan datos (archivo o eleccion)"}, status=400)

        try:
            # 1. Validamos la elección
            eleccion_obj = Eleccion.objects.filter(anio=anio_eleccion).first()
            if not eleccion_obj:
                return Response({"error": f"No existe la elección registrada para el año {anio_eleccion}"}, status=404)

            decoded_file = archivo.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            
            count = 0
            partidos_afectados = set()

            with transaction.atomic():
                for row in reader:
                    # 2. Buscamos la pregunta por ID (dentro de la elección correcta)
                    pregunta = Pregunta.objects.filter(texto__iexact=row['pregunta_texto'].strip(), eleccion=eleccion_obj).first()
                    
                    # 3. Buscamos el partido por NOMBRE o SIGLA (ignora mayúsculas/minúsculas)
                    nombre_partido = row['partido'].strip()
                    partido = Partido.objects.filter(nombre__iexact=nombre_partido).first()
                    if not partido:
                        partido = Partido.objects.filter(sigla__iexact=nombre_partido).first()
                    
                    if pregunta and partido:
                        # 4. Crear o actualizar la respuesta
                        PartidoRespuesta.objects.update_or_create(
                            pregunta=pregunta,
                            partido=partido,
                            defaults={
                                'valor': int(row['valor']),
                                'fuente': row.get('fuente', '')
                            }
                        )
                        count += 1
                        partidos_afectados.add(partido)

                # 5. Recalcular caché de posiciones al finalizar la carga
                for p in partidos_afectados:
                    self.actualizar_posicion_cache(p, eleccion_obj)

            return Response({
                "status": "Éxito", 
                "msg": f"Se procesaron {count} respuestas. Se actualizó la posición de {len(partidos_afectados)} partidos."
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def actualizar_posicion_cache(self, partido, eleccion):
        """
        Calcula el promedio de las respuestas del partido y guarda su posición.
        """
        respuestas = PartidoRespuesta.objects.filter(
            partido=partido, 
            pregunta__eleccion=eleccion
        )
        
        if respuestas.exists():
            posX, posY = calcular_posicion(respuestas)
            
            PartidoPosicion.objects.update_or_create(
                partido=partido,
                defaults={
                    'posicion_x': posX,
                    'posicion_y': posY
                }
            )
        
class ImportarPreguntasView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        anio_eleccion = request.data.get('anio') # El año para asociar las preguntas

        if not archivo or not anio_eleccion:
            return Response({"error": "Faltan datos: archivo y anio son requeridos"}, status=400)

        try:
            # Buscamos la elección
            eleccion_obj = Eleccion.objects.filter(anio=anio_eleccion).first()
            if not eleccion_obj:
                return Response({"error": f"No existe elección para el año {anio_eleccion}"}, status=404)

            decoded_file = archivo.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            
            creadas = 0
            
            with transaction.atomic():
                for row in reader:
                    # Usamos update_or_create para evitar duplicar preguntas si se sube el CSV dos veces
                    Pregunta.objects.update_or_create(
                        texto=row['texto'],
                        eleccion=eleccion_obj,
                        defaults={
                            'eje': row['eje'].upper(), # 'X' o 'Y'
                            'direccion': int(row['direccion']), # 1 o -1
                            'categoria': row.get('categoria', 'General'), # Evita el error de null
                            'estado': row.get('estado', 'activa')
                        }
                    )
                    creadas += 1
            
            return Response({
                "status": "Éxito", 
                "msg": f"Se importaron {creadas} preguntas para la elección {anio_eleccion}."
            })
        except Exception as e:
            return Response({"error": f"Error al importar preguntas: {str(e)}"}, status=500)