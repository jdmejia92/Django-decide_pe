from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from core.models import Eleccion, Partido, Candidato, Region, PartidoMetadata
from quiz.models import Pregunta, PartidoRespuesta, PartidoPosicion
from quiz.utils import calcular_posicion
from core.serializers import PartidoMetadataImportSerializer
from django.db import transaction
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
        
class ImportarCandidatosView(APIView):
    def post(self, request):
        archivo = request.FILES.get('archivo')
        
        if not archivo or not archivo.name.endswith('.csv'):
            return Response({"error": "Sube un archivo CSV válido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Leer y decodificar el archivo
            data_set = archivo.read().decode('UTF-8-sig') # 'UTF-8-sig' elimina el BOM de Excel
            io_string = io.StringIO(data_set)
            
            # --- MEJORA: Detección segura de delimitador ---
            try:
                primeras_lineas = io_string.read(2048)
                dialect = csv.Sniffer().sniff(primeras_lineas, delimiters=',;')
                io_string.seek(0)
                lector = csv.reader(io_string, dialect)
            except csv.Error:
                # Si falla el sniffer, asumimos coma por defecto
                io_string.seek(0)
                lector = csv.reader(io_string, delimiter=',')
            
            next(lector) # Saltar cabecera
            
            contador_nuevos = 0
            contador_actualizados = 0
            errores = []

            with transaction.atomic():
                for i, row in enumerate(lector, start=2):
                    # Ignorar filas vacías o mal formadas
                    if not row or len(row) < 8:
                        continue
                    
                    try:
                        # Limpiar espacios de cada columna
                        nombres, apellidos, cargo, numero, sigla_partido, nombre_region, foto, hojavida = [col.strip() for col in row[:8]]

                        # Buscar Partido y Región
                        partido = Partido.objects.get(sigla__iexact=sigla_partido)
                        region = Region.objects.filter(nombre__icontains=nombre_region).first() if nombre_region else None

                        # Evitar duplicados con update_or_create
                        candidato, created = Candidato.objects.update_or_create(
                            nombres=nombres,
                            apellidos=apellidos,
                            cargo=cargo,
                            partido=partido, # Agregamos partido al criterio de búsqueda por seguridad
                            defaults={
                                'numero': int(numero) if numero and numero.isdigit() else None,
                                'region_rel': region,
                                'foto': foto,
                                'hojavida': hojavida
                            }
                        )
                        
                        if created:
                            contador_nuevos += 1
                        else:
                            contador_actualizados += 1
                            
                    except Partido.DoesNotExist:
                        errores.append(f"Fila {i}: Partido '{sigla_partido}' no existe.")
                    except Exception as e:
                        errores.append(f"Fila {i}: {str(e)}")

            return Response({
                "message": f"Proceso completado. {contador_nuevos} nuevos, {contador_actualizados} actualizados.",
                "errores": errores
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error al leer el archivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ImportarMetadataView(APIView):
    def post(self, request):
        archivo = request.FILES.get('archivo')
        
        if not archivo or not archivo.name.endswith('.csv'):
            return Response({"error": "Sube un archivo CSV válido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_set = archivo.read().decode('utf-8-sig')
            io_string = io.StringIO(data_set)
            
            # Detección de delimitador
            try:
                sample = io_string.read(2048)
                dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                io_string.seek(0)
                lector = csv.reader(io_string, dialect)
            except Exception:
                io_string.seek(0)
                lector = csv.reader(io_string, delimiter=',')

            next(lector, None) # Saltar cabecera
            
            procesados = 0
            errores = []

            with transaction.atomic():
                for i, row in enumerate(lector, start=2):
                    if not row or len(row) < 1:
                        continue
                    
                    try:
                        # Extraer datos del CSV (ajusta el orden si es necesario)
                        # sigla, candidato, lider, color, plan_url, cand_key, anio, tipo
                        sigla = row[0].strip()
                        
                        # Buscamos el objeto Partido por sigla
                        partido = Partido.objects.get(sigla__iexact=sigla)

                        # Preparamos los datos para el Serializer
                        datos_fila = {
                            'partido': partido.id,
                            'candidato_presidencial': row[1].strip() if len(row) > 1 else None,
                            'lider_partido': row[2].strip() if len(row) > 2 else None,
                            'color_primario': row[3].strip() if len(row) > 3 and row[3] else '#000000',
                            'plan_gobierno': row[4].strip() if len(row) > 4 else None,
                            'candidato_key': row[5].strip() if len(row) > 5 and row[5] else 'DEFAULT_CANDIDATE',
                            'anio_fundacion': int(row[6].strip()) if len(row) > 6 and row[6].strip().isdigit() else None,
                            'tipo_organizacion': row[7].strip() if len(row) > 7 and row[7] else 'Partido Político'
                        }

                        # Instanciamos el Serializer para validar
                        serializer = PartidoMetadataImportSerializer(data=datos_fila)
                        
                        if serializer.is_valid():
                            # Usamos update_or_create con los datos ya validados
                            PartidoMetadata.objects.update_or_create(
                                partido=partido,
                                defaults=serializer.validated_data
                            )
                            procesados += 1
                        else:
                            # Capturamos errores de validación (ej: URL mal formada)
                            errores.append(f"Fila {i} ({sigla}): {serializer.errors}")

                    except Partido.DoesNotExist:
                        errores.append(f"Fila {i}: La sigla '{sigla}' no existe.")
                    except Exception as e:
                        errores.append(f"Fila {i}: Error -> {str(e)}")

            return Response({
                "status": "proceso completado",
                "metadata_procesada": procesados,
                "errores": errores
            }, status=status.HTTP_200_OK if not errores else status.HTTP_207_MULTI_STATUS)

        except Exception as e:
            return Response({"error": f"Error crítico: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)