import math

def calcular_posicion(queryset_respuestas):
    """
    Calcula las coordenadas X e Y basándose en las respuestas proporcionadas.
    """
    respuestas_activas = queryset_respuestas.filter(pregunta__estado='activa').select_related('pregunta')
    
    def procesar_eje(nombre_eje):
        eje_data = respuestas_activas.filter(pregunta__eje=nombre_eje)
        
        total = sum(r.valor * r.pregunta.direccion for r in eje_data)
        
        count = eje_data.exclude(valor=0).count()
        
        if count == 0:
            return 0.0
            
        resultado = (total / (count * 2)) * 100
        return max(-100, min(100, float(resultado)))

    return procesar_eje('X'), procesar_eje('Y')

def obtener_ranking_partidos(usuario_x, usuario_y):
    """
    Compara las coordenadas del usuario con las posiciones de los partidos.
    """
    from .models import PartidoPosicion
    
    posiciones = PartidoPosicion.objects.select_related('partido').all()
    ranking = []
    
    distancia_maxima = math.sqrt(200**2 + 200**2) 

    for pos in posiciones:
        px = float(pos.posicion_x or 0)
        py = float(pos.posicion_y or 0)
        ux = float(usuario_x)
        uy = float(usuario_y)

        # Distancia euclidiana
        distancia = math.sqrt((px - ux)**2 + (py - uy)**2)
        
        afinidad = (1 - (distancia / distancia_maxima)) * 100
        
        ranking.append({
            'partido': pos.partido.nombre,
            'sigla': pos.partido.sigla,
            'compatibilidad': round(afinidad, 2),
            'posicion': {'x': px, 'y': py}
        })
    
    ranking.sort(key=lambda x: x['compatibilidad'], reverse=True)
    
    return ranking