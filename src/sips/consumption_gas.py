from src.sips.reader import BaseReader


class ConsumptionGasReader(BaseReader):
    FIELDS = [
        "Cups",  # Código Universal de Punto de Suministro. X(22)
        "fechaInicioMesConsumo",  # Fecha inicio del periodo mensual de consumo. AAAA-MM-DD
        "fechaFinMesConsumo",  # Fecha fin del periodo mensual de consumo. AAAA-MM-DD
        "codigoTarifaPeaje",  # Código que informa sobreel peaje de gas. X(2)
        "consumoEnWhP1",  # Consumo con periodicidad mensual en periodo 1 en Wh sin decimales. 9(14)
        "consumoEnWhP2",  # Consumo con periodicidad mensual en periodo 2 en Wh sin decimales. 9(14)
        "caudalMedioEnWhdia",  # Caudal medio en el periodo indicado en Wh/dia. Sin decimales. 9(14)
        "caudaMinimoDiario",  # Caudal minimo diario medido en Wh/dia. Sin decimales. 9(14)
        "caudaMaximoDiario",  # Caudal máximo diario medido en Wh/dia. Sin decimales. 9(14)
        "porcentajeConsumoNocturno",  # 0-100. Sin decimales. 9(3)
        "codigoTipoLectura",  # Información sobre la procedencia de la lectura. X(2)
        # "R" - Real
        # "E" - Estimada
    ]
