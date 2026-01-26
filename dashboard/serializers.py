from rest_framework import serializers

class CargaMasivaSerializer(serializers.Serializer):
    """
    Este serializer valida la subida del archivo desde el Dashboard.
    """
    archivo = serializers.FileField()
    anio = serializers.IntegerField()

class EstadisticasDashboardSerializer(serializers.Serializer):
    """
    Para enviar un resumen ejecutivo al frontend del administrador.
    """
    total_usuarios = serializers.IntegerField()
    total_partidos = serializers.IntegerField()
    test_completados = serializers.IntegerField()
    test_en_progreso = serializers.IntegerField()