from datetime import date, timedelta
from typing import Dict, Iterator, List

import pydantic
from pydantic import BaseModel
from pydantic.types import condecimal, constr

from src.sips.reader import BaseReader, SIPSTypes


class ConsumptionElectricityResponse(BaseModel):
    cups: constr(min_length=20, max_length=22)
    start_date: pydantic.types.date | None
    end_date: pydantic.types.date | None
    consumption_p1: condecimal(decimal_places=2, ge=0) = 0
    consumption_p2: condecimal(decimal_places=2, ge=0) = 0
    consumption_p3: condecimal(decimal_places=2, ge=0) = 0
    consumption_p4: condecimal(decimal_places=2, ge=0) = 0
    consumption_p5: condecimal(decimal_places=2, ge=0) = 0
    consumption_p6: condecimal(decimal_places=2, ge=0) = 0

    @property
    def annual_consumption(self) -> int:
        return (
            self.consumption_p1
            + self.consumption_p2
            + self.consumption_p3
            + self.consumption_p4
            + self.consumption_p5
            + self.consumption_p6
        )

    @property
    def analyzed_days(self) -> int:
        delta = self.end_date - self.start_date
        return delta.days


class ConsumptionElectricityReader(BaseReader):
    FIELDS = [
        "cups",  # Código Universal de Punto de Suministro. X(22)
        "fechaInicioMesConsumo",  # Fecha inicio del periodo mensual de consumo. AAAA-MM-DD
        "fechaFinMesConsumo",  # Fecha fin del periodo mensual de consumo. AAAA-MM-DD
        "codigoTarifaATR",  # Código de la tarifa de acceso vigente en el mes. X(3)
        "consumoEnergiaActivaEnWhP1",
        # Consumo de energía activa con periodicidad mensual en periodo 1 en Wh sin decimales. S9(14)
        "consumoEnergiaActivaEnWhP2",
        # Consumo de energía activa con periodicidad mensual en periodo 2 en Wh sin decimales. S9(14)
        "consumoEnergiaActivaEnWhP3",
        # Consumo de energía activa con periodicidad mensual en periodo 3 en Wh sin decimales. S9(14)
        "consumoEnergiaActivaEnWhP4",
        # Consumo de energía activa con periodicidad mensual en periodo 4 en Wh sin decimales. S9(14)
        "consumoEnergiaActivaEnWhP5",
        # Consumo de energía activa con periodicidad mensual en periodo 5 en Wh sin decimales. S9(14)
        "consumoEnergiaActivaEnWhP6",
        # Consumo de energía activa con periodicidad mensual en periodo 6 en Wh sin decimales. S9(14)
        "consumoEnergíaReactivaEnVArhP1",
        # Consumo de energía reactiva con periodicidad mensual en periodo 1 en VArh sin decimales. 9(14)
        "consumoEnergíaReactivaEnVArhP2",
        # Consumo de energía reactiva con periodicidad mensual en periodo 2 en VArh sin decimales. 9(14)
        "consumoEnergíaReactivaEnVArhP3",
        # Consumo de energía reactiva con periodicidad mensual en periodo 3 en VArh sin decimales. 9(14)
        "consumoEnergíaReactivaEnVArhP4",
        # Consumo de energía reactiva con periodicidad mensual en periodo 4 en VArh sin decimales. 9(14)
        "consumoEnergíaReactivaEnVArhP5",
        # Consumo de energía reactiva con periodicidad mensual en periodo 5 en VArh sin decimales. 9(14)
        "consumoEnergíaReactivaEnVArhP6",
        # Consumo de energía reactiva con periodicidad mensual en periodo 6 en VArh sin decimales. 9(14)
        "potenciaDemandadaEnWP1",  # Potencia demandada en el mes para el periodo 1 en vatios sin decimales. 9(14)
        "potenciaDemandadaEnWP2",  # Potencia demandada en el mes para el periodo 2 en vatios sin decimales. 9(14)
        "potenciaDemandadaEnWP3",  # Potencia demandada en el mes para el periodo 3 en vatios sin decimales. 9(14)
        "potenciaDemandadaEnWP4",  # Potencia demandada en el mes para el periodo 4 en vatios sin decimales. 9(14)
        "potenciaDemandadaEnWP5",  # Potencia demandada en el mes para el periodo 5 en vatios sin decimales. 9(14)
        "potenciaDemandadaEnWP6",  # Potencia demandada en el mes para el periodo 6 en vatios sin decimales. 9(14)
        "codigoDHEquipoDeMedida",  # Información de la discriminación horaria del equipo de medida. X(1)
        "codigoTipoLectura",  # Información sobre la procedencia de la lectura. X(2)
    ]

    def get(self, cups: List[str]) -> Dict:
        reader = self.fetch(SIPSTypes.CONSUMOS_ELECTRICIDAD, cups)

        data = dict()

        for cup in cups:
            filtered_by_cup_results = filter(lambda d: d["cups"] == cup, reader)
            data[cup] = self._get_by_cup(cup, filtered_by_cup_results)

        return data

    @staticmethod
    def _get_by_cup(cup: str, results: Iterator) -> ConsumptionElectricityResponse:
        results = sorted(
            results,
            key=lambda d: date.fromisoformat(d["fechaFinMesConsumo"]),
        )
        last_result = results[-1]
        max_date = date.fromisoformat(last_result["fechaFinMesConsumo"])
        expected_min_date = max_date - timedelta(days=365)
        filtered_results = list(
            filter(
                lambda d: date.fromisoformat(d["fechaInicioMesConsumo"])
                >= expected_min_date,
                results,
            )
        )
        min_date = date.fromisoformat(filtered_results[0]["fechaInicioMesConsumo"])

        response = ConsumptionElectricityResponse(
            cups=cup, start_date=min_date, end_date=max_date
        )
        for row in filtered_results:
            response.consumption_p1 += int(row["consumoEnergiaActivaEnWhP1"]) / 1000
            response.consumption_p2 += int(row["consumoEnergiaActivaEnWhP2"]) / 1000
            response.consumption_p3 += int(row["consumoEnergiaActivaEnWhP3"]) / 1000
            response.consumption_p4 += int(row["consumoEnergiaActivaEnWhP4"]) / 1000
            response.consumption_p5 += int(row["consumoEnergiaActivaEnWhP5"]) / 1000
            response.consumption_p6 += int(row["consumoEnergiaActivaEnWhP6"]) / 1000

        return response
