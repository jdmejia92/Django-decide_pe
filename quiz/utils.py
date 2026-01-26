import math

def calcular_posicion(queryset_respuestas):
    """
    Calcula las coordenadas X e Y basándose en las respuestas proporcionadas.
    Funciona tanto para UserAnswer como para PartyAnswer.
    """
    respuestas_activas = queryset_respuestas.filter(pregunta__estado='activa')
    
    def procesar_eje(nombre_eje):
        eje_data = respuestas_activas.filter(pregunta__eje=nombre_eje)
        # Suma de (valor * direccion)
        total = sum(r.valor * r.pregunta.direccion for r in eje_data)
        # Conteo de preguntas con valor distinto a 0
        count = eje_data.exclude(valor=0).count()
        
        if count == 0:
            return 0.0
            
        # Fórmula: (Suma / (Count * 2)) * 100
        resultado = (total / (count * 2)) * 100
        return max(-100, min(100, resultado))

    return procesar_eje('X'), procesar_eje('Y')

def obtener_ranking_partidos(usuario_x, usuario_y):
    """
    Compara las coordenadas del usuario con las posiciones de los partidos
    registradas en PartidoPosicion.
    """
    from .models import PartidoPosicion
    # Traemos las posiciones, incluyendo los datos del partido para no hacer 
    # muchas consultas a la BD (select_related)
    posiciones = PartidoPosicion.objects.select_related('partido').all()
    ranking = []
    
    # Distancia máxima en plano 200x200
    distancia_maxima = math.sqrt(200**2 + 200**2) 

    for pos in posiciones:
        # Convertimos Decimal a float para el cálculo matemático
        px = float(pos.posicion_x)
        py = float(pos.posicion_y)
        ux = float(usuario_x)
        uy = float(usuario_y)

        # Distancia euclidiana
        distancia = math.sqrt((px - ux)**2 + (py - uy)**2)
        
        # Cálculo de afinidad (0% a 100%)
        afinidad = (1 - (distancia / distancia_maxima)) * 100
        
        ranking.append({
            'partido': pos.partido.nombre,
            'sigla': pos.partido.sigla,
            # 'logo': pos.partido.logo.url if pos.partido.logo else None, # Descomenta si tienes logo
            'compatibilidad': round(afinidad, 2),
            'posicion': {'x': px, 'y': py}
        })
    
    # Ordenar por el que tiene más match
    ranking.sort(key=lambda x: x['compatibilidad'], reverse=True)
    
    return ranking