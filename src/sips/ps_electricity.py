from typing import Dict, List

from src.sips.reader import BaseReader, SIPSTypes


class PsElectricityReader(BaseReader):
    FIELDS = [
        "codigoEmpresaDistribuidora",  # Código alfanumérico de longitud 4 que identifica el agente distribuidor. X(4)
        "cups",  # Código Universal de Punto de Suministro. X(22)
        "nombreEmpresaDistribuidora",  # distribuidores eléctricos del Minetur. X(60)
        "codigoPostalPS",  # Código postal del punto de suministro. X(5)
        "municipioPS",  # Municipio del punto de suministro. X(5)
        "codigoProvinciaPS",  # X(2)
        "fechaAltaSuministro",  # AAAA-MM-DD
        "codigoTarifaATREnVigor",  # Código de la tarifa de acceso en vigor. X(3)
        "codigoTensionV",  # Código de la tensión en voltios de la conexión del punto de suministro a las redes. X(2)
        "potenciaMaximaBIEW",  # Potencia máxima en vatios del punto de suministro. 9(11)
        "potenciaMaximaAPMW",  # Potencia máxima en vatios del punto de suministro. 9(11)
        "codigoClasificacionPS",  # Código de la clasificación del punto de suministro. X(2)
        "codigoDisponibilidadICP",  # Disponibilidad de Interruptor de Control de Potencia. X(1)
        "tipoPerfilConsumo",  # Se informará según los siguientes valores: "Pa" , "Pb", "Pc", "Pd" o vacio. X(2)
        "valorDerechosExtensionW",
        # Valor de los derechos de extensión en vatios que tenga reconocidos el punto de suministro. 9(11)
        "valorDerechosAccesoW",
        # Valor de los derechos de acceso en vatios que tenga reconocidos el punto de suministro. 9(11)
        "codigoPropiedadEquipoMedida",  # Propietario del equipo de medida. X(1)
        "codigoPropiedadICP",
        # Propiedad de Interruptor de Control de Potencia, que incluye tipo de propietario del ICP. X(1)
        "potenciasContratadasEnWP1",
        # Potencia contratada para el periodo 1 de discriminación horaria, en vatios sin decimales. S(14)
        "potenciasContratadasEnWP2",
        # Potencia contratada para el periodo 2 de discriminación horaria, en vatios sin decimales. S(14)
        "potenciasContratadasEnWP3",
        # Potencia contratada para el periodo 3 de discriminación horaria, en vatios sin decimales. S(14)
        "potenciasContratadasEnWP4",
        # Potencia contratada para el periodo 4 de discriminación horaria, en vatios sin decimales. S(14)
        "potenciasContratadasEnWP5",
        # Potencia contratada para el periodo 5 de discriminación horaria, en vatios sin decimales. S(14)
        "potenciasContratadasEnWP6",
        # Potencia contratada para el periodo 6 de discriminación horaria, en vatios sin decimales. S(14)
        "fechaUltimoMovimientoContrato",
        # Fecha del último movimiento de contratación a efectos del último tarifarios. AAAA-MM-DD
        "fechaUltimoCambioComercializador",  # Fecha del último cambio de comercializador. AAAA-MM-DD
        "fechaLimiteDerechosReconocidos",  # Fecha límite de los derechos de extensión reconocidos. AAAA-MM-DD
        "fechaUltimaLectura",  # Fecha de la última lectura firme. AAAA-MM-DD
        "informacionImpagos",  # Información relativa a los impagos en que los consumidores hayan incurrido. X(255)
        "importeDepositoGarantiaEuros",
        # Importe del depósito de garantía suscrito por el titular del punto de suministro, en euros. 9(9)
        "tipoIdTitular",  # Tipo de identificador del titular del contrato. X(2)
        "esViviendaHabitua",  # En relación al uso del punto de suministro cuando el titular es persona física. X(1)
        "codigoComercializadora",  # Código identifica el agente comercializador del punto de suministro. X(4)
        "codigoTelegestion",
        # Información sobre la disponibilidad del equipo de medida efectivamente integrado en el sistema de telegestión.
        # X(2)
        "codigoFasesEquipoMedida",
        # Código que identifica si el equipo de medida es monofásico(M) o trifásico(T). X(1)
        "codigoAutoconsumo",
        # Información relativa al acogimiento o no a una modalidad de autoconsumo y particularización del tipo. X(2)
        "codigoTipoContrato",
        # Información sobre el tipo de contrato de acceso (i.e. anual, eventual, temporada, etc.) X(2)
        "codigoPeriodicidadFacturacion",  # Periodicidad de la facturación: mensual o bimestral. X(2)
        "codigoBIE",  # Código del Boletín del Instalador Eléctrico. X(30)
        "fechaEmisionBIE",  # Fecha de emisión del Boletín del Instalador Eléctrico. AAAA-MM-DD
        "fechaCaducidadBIE",  # Fecha de caducidad del Boletín del Instalador Eléctrico. AAAA-MM-DD
        "codigoAPM",  # Código del Acta de Puesta en Marcha. X(30)
        "fechaEmisionAPM",  # Fecha de emisión del Acta de Puesta en Marcha. AAAA-MM-DD
        "fechaCaducidadAPM",  # Fecha de caducidad del Acta de Puesta en Marcha. AAAA-MM-DD
        "relacionTransformacionIntensidad",  # Se indica la intensidad del primario/ intensidad del secundario. X(15)
        "Cnae",  # Clasificación Nacional de Actividades Económicas. X(4)
        "codigoModoControlPotencia",  # X(1)
        # "1" - ICP ,
        # "2" - Maximetro,
        # "3" - Control de potencia en contador de telegestión,
        # "4" - Sin control de potencia.
        "potenciaCGPW",  # Es la potencia en vatios permitida en la Caja General de Protección. 9(11)
        "codigoDHEquipoDeMedida",  # Información de la discriminación horaria del equipo de medida. X(1)
        "codigoAccesibilidadContador",  # Información sobre la accesibilidad del contador. X(1)
        # "1" - Punto de suministro accesible,
        # "2" - Contador no accesible (para acceder se necesita la colaboración del usuario),
        # "3" - Accesibilidad condicionada.
        "codigoPSContratable",
        # Indicativo que define si el Punto de Suministro es contratable tras el cierre de un expediente. X(1)
        # "0" - No contratable
        # "1" - Contratable.
        "motivoEstadoNoContratable",
        # Información sobre el motivo del estado "No contratable" tras el cierre de un expediente (i.e. falta
        # documentación, etc.) X(255)
        "codigoTensionMedida",
        # Código de la tensión del Equipo de medida situado a una tensión distinta a la del suministro. X(2)
        "codigoClaseExpediente",  # Tipo de expediente abierto X(1)
        # "I" - Inspección,
        # "N" - Nuevos suministros
        "codigoMotivoExpediente",
        # Si existe un expediente abierto se especificará el motivo del expediente con alguno de los códigos X(2)
        # "01" - Aumento potencia
        # "02" - Cambio tensión
        # "03" - Cambio tarifa
        # "04" - Nuevo suministro
        # "05" - Colectivo nueva construcción
        # "06" - Colectivo electrificación rural
        # "07" - Informativo Plan urbanístico
        # "08" - Informativo Plan industrial
        # "09" - Informativo Productor de Régimen Especial
        # "10" - Colectivo reconstrucción vivienda
        # "11" - TCT No relacionado a NNSS
        # "12" - TCT Relacionado a NNSS
        # "13" - Colectivo renovación de Instalaciones de enlace varios suministros
        # "14" - Renovación de instalaciones de enlace
        "codigoTipoSuministro",  # Descriptor del tipo de suministro X(2)
        "aplicacionBonoSocial"  # Bono social aplicado por el comercializador de referencia. X(1)
        # “0” - no se aplica bono social
        # “1” - sí se aplica bono social.
    ]

    def get(self, cups: List[str]) -> Dict:
        result = self.fetch(SIPSTypes.PS_ELECTRICIDAD, cups)
        return BaseReader._get(result)
