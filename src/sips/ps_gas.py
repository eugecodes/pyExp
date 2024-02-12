from src.sips.reader import BaseReader


class PsGasReader(BaseReader):
    FIELDS = [
        "codigoEmpresaDistribuidora",  # Código SIFCO de la Empresa Distribuidora de Gas. X(4)
        "nombreEmpresaDistribuidora",  # X(60)
        "cups",  # Código Universal de Punto de Suministro. X(22)
        "codigoProvinciaPS",  # X(2)
        "desProvinciaPS",  # Descriptor del código Provincia donde se ubica el punto de suministro X(40)
        "codigoPostalPS",  # Código postal del punto de suministro. X(5
        "municipioPS",  # Municipio del punto de suministro. X(5)
        "desmunicipioPS",  # Descriptor del código INE que hace referencia al municipio donde se ubica el
        # punto de suministro. X(60)
        "tipoViaPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(5)
        "viaPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(50)
        "numFincaPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(4)
        "portalPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(5)
        "escaleraPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(5)
        "pisoPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(5)
        "puertaPS",  # Esta información sobre el tipo de vía debe referirse a la dirección de la ubicación del
        # punto de suministro. X(5)
        "codigoPresion",  # Código de la presión (en bares o rango). X(2)
        "codigoPeajeEnVigor",  # Código del peaje en vigor. X(2)
        "caudalMaximoDiarioEnWh",  # Caudal máximo diario contratado (en Wh/día). 9(14)
        "caudalHorarioEnWh",  # Caudal horario en Wh. 9(14)
        "derechoTUR",  # Cumple con las condiciones para ser suministrado a la Tarifa de Último Recurso (TUR). X(1)
        "fechaUltimaInspeccion",  # Fecha de la última revisión y de la última inspección de las instalaciones
        # receptoras individuales. AAAA-MM-DD
        "codigoResultadoInspeccion",  # Código del resultado de la última revisión y de la última inspección de
        # las instalaciones receptoras. X(2)
        "tipoPerfilConsumo",  # Código del tipo de perfil de consumo. X(2)
        "codigoContador",  # Código identificador del equipo de medida. X(17)
        "calibreContador",  # Los rangos de medida (valores máximo y mínimo dentro de los cuales el contador es
        # válido para efectuar la medición dentro de las tolerancias admisibles) se representan con la letra G
        # seguido de un número que lo relaciona con el caudal máximo en m3/h. X(50)
        "tipoContador",  # membrana, pistones, turbinas, ultrasónicos, másicos, etc. X(15)
        "propiedadEquipoMedida",  # Información sobre la propiedad del equipo de medida.  X(1)
        # "1" -Distribuidor,
        # "2" -Consumidor,
        # "3" -Comercializador,
        # "4" -Otros.
        "codigoTelemedida",  # Información sobre disponibilidad de telemedida.  X(1)
        # "0" - en caso de no disponer de telemedida,
        # "1" - en caso de disponer de telemedida.
        "fechaUltimoMovimientoContrato",  # Día, mes y año del último cambio de los parámetros relativos a la
        # contratación de la tarifa de acceso, pudiendo ser estos parámetros la tarifa de acceso en si misma,
        # el nivel de consumo de referencia aplicable al cliente, los caudales contratados y la presión de suministro.
        # Nota: un cambio comercializador de sin modificaciones en el contrato de acceso no desencadena un movimiento
        # de contrato y no estaría reflejado en este campo.  AAAA-MM-DD
        "fechaUltimoCambioComercializador",  # Fecha del último cambio de comercializador.
        # Nota: un cambio de comercializador desencadenado por operaciones societarias, no computa como cambio
        # de comercializador. Los traspasos a la CUR por la extinción de la habilitación del comercializador implicado,
        # tampoco computan como cambio de comercializador. Ninguno de estos movimientos debería estar reflejado
        # en este campo. AAAA-MM-DD
        "informacionImpagos",  # Información relativa a los impagos en que los consumidores hayan incurrido. X(255)
        "idTipoTitular",  # Tipo de identificador del titular. X(2)
        # NI" - NIF
        # "NV" - N.I.V.A
        # "OT" - Otro
        # "PS" - Pasaporte
        # "NE" - NIE
        "idTitular",  # Número que identifica al titular del punto de suministro, tanto si es persona física
        # como si es persona jurídica X(14)
        "nombreTitular",  # Nombre, o en su caso denominación social y forma societaria,
        # del titular del punto de suministro.   X(30)
        "apellido1Titular",  # Primer apellido del titular del punto de suministro X(40)
        "apellido2Titular",  # Segundo apellido del titular del punto de suministro X(30)
        "codigoProvinciaTitular",  # X(2)
        "desProvinciaTitular",  # Descriptor de la provincia del titular del punto de suministro. X(40)
        "codigoPostalTitular",  # Código postal del Titular del punto de suministro X(5)
        "municipioTitular",  # Municipio del titular del punto de suministro X(5)
        "desMunicipioTitular",  # Descriptor del municipio del titular del punto de suministro. X(60)
        "tipoViaTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(5)
        "viaTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(50)
        "numFincaTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(4)
        "portalTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(5)
        "escaleraTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(5)
        "pisoTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(5)
        "puertaTitular",  # Debe ser relativa al titular y no a la ubicación del punto de suministro. X(5)
        "esViviendaHabitual",  # En relación al uso del punto de suministro cuando el titular es persona física. X(1)
        # “0” - cuando no sea vivienda habitual,
        # “1” - cuando sea vivienda habitual.
        "Cnae",  # Clasificación Nacional de Actividades Económicas X(4)
        "tipoCorrector",  # El corrector es el equipo que asociado a un contador de gas convierte los m3 totalizados,
        # en m3 en condiciones de referencia. X(3)
        # - Conversor T (de uso limitado): Utilizan la variable de temperatura para la conversión a condiciones de
        # referencia. El resto de valores de cálculo son fijos.
        # - Conversor P (de uso limitado): Utilizan la variable de presión para la conversión a condiciones de
        # referencia.
        # El resto de valores de cálculo son fijos.
        # - Conversor PT: Utilizan las dos variables, presión y temperatura, para la conversión a condiciones de
        # referencia. El valor del factor de compresibilidad “Z” es de 1.
        # - Conversor PTZ: Utiliza las variables de presión, temperatura y el factor de compresibilidad “Z”
        # (función de la composición del gas, presión y temperatura), para la conversión a condiciones de referencia.
        # - Conversor PTZ asociado a equipo de análisis de gas (cromatógrafo): Al estar asociado a un equipo de
        # cromatografía permite dar los valores en energía (kWh) además de los metros cúbicos en condiciones de
        # referencia.
        "codigoAccesibilidadContador",  # Información sobre la accesibilidad del contador. X(1)
        # "1" - Punto de suministro accesible
        # "2" - Contador no accesible (para acceder se necesita la colaboración del usuario)
        # "3" - Accesibilidad condicionada
        "conectadoPlantaSatelite",  # Si el punto está conectado a una planta satélite de gas natural. X(1)
        # "0" - No está conectado a una planta satélite
        # "1" - Si está conectado a una planta satélite
        "Pctd",  # Punto de conexión Transporte-Distribución. X(255)
        "presionMedida",  # Presión del contador, necesaria para calcular el volumen corregido del gas cuando
        # no hay equipo converso. X(4)
    ]
