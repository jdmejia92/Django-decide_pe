import math

def calcular_posicion(queryset_respuestas):
    """
    Calcula las coordenadas X e Y basándose en las respuestas proporcionadas.
    Normaliza el resultado entre -100 y 100.
    """
    respuestas_activas = queryset_respuestas.filter(pregunta__estado='activa').select_related('pregunta')
    
    def procesar_eje(nombre_eje):
        eje_data = respuestas_activas.filter(pregunta__eje=nombre_eje)
        
        # Multiplicamos el valor de la respuesta por la dirección de la pregunta
        total = sum(r.valor * r.pregunta.direccion for r in eje_data)
        
        count = eje_data.count()
        
        if count == 0:
            return 0.0
            
        # El valor máximo posible es count * 2 (si todas son "Muy a favor" = 2)
        resultado = (total / (count * 2)) * 100
        return max(-100, min(100, float(resultado)))

    return procesar_eje('X'), procesar_eje('Y')

def obtener_ranking_partidos(usuario_x, usuario_y):
    """
    Compara las coordenadas del usuario con las posiciones de los partidos
    y devuelve el formato exacto que espera Resultado.jsx
    """
    from .models import PartidoPosicion
    
    posiciones = PartidoPosicion.objects.select_related('partido').all()
    ranking = []
    
    # La distancia máxima posible en un plano de -100 a 100 es 
    # la diagonal de (-100, -100) a (100, 100)
    # dist = sqrt((100 - (-100))^2 + (100 - (-100))^2) = sqrt(200^2 + 200^2)
    distancia_maxima = math.sqrt(80000)

    for pos in posiciones:
        px, py = float(pos.posicion_x or 0), float(pos.posicion_y or 0)
        ux, uy = float(usuario_x), float(usuario_y)

        # Distancia euclidiana clásica
        distancia = math.sqrt((px - ux)**2 + (py - uy)**2)
        
        # Invertimos la distancia para obtener afinidad (0 a 100)
        afinidad = (1 - (distancia / distancia_maxima)) * 100
        
        ranking.append({
            'id': pos.partido.id,
            'nombre': pos.partido.nombre,
            'sigla': pos.partido.sigla,
            'candidato_presidencial': getattr(pos.partido, 'candidato_presidencial', 'Candidato por definir'),
            'match_percentage': int(afinidad),
            'posicion': {'x': px, 'y': py}
        })
    
    ranking.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return ranking