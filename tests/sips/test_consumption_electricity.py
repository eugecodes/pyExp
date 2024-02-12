from datetime import date

from src.sips.consumption_electricity import ConsumptionElectricityReader


def test_consumption_electricity_reader_get_by_cup(mocker):
    request_mock = mocker.patch("src.sips.reader.requests")
    request_mock.get.return_value.status_code = 200
    request_mock.get.return_value.text = (
        """cups,fechaInicioMesConsumo,fechaFinMesConsumo,codigoTarifaATR,"""
    )
    """consumoEnergiaActivaEnWhP1,consumoEnergiaActivaEnWhP2,consumoEnergiaActivaEnWhP3,"""
    """consumoEnergiaActivaEnWhP4,consumoEnergiaActivaEnWhP5,consumoEnergiaActivaEnWhP6,"""
    """consumoEnergiaReactivaEnVArhP1,consumoEnergiaReactivaEnVArhP2,consumoEnergiaReactivaEnVArhP3,"""
    """consumoEnergiaReactivaEnVArhP4,consumoEnergiaReactivaEnVArhP5,consumoEnergiaReactivaEnVArhP6,"""
    """potenciaDemandadaEnWP1,potenciaDemandadaEnWP2,potenciaDemandadaEnWP3,potenciaDemandadaEnWP4,"""
    """potenciaDemandadaEnWP5,potenciaDemandadaEnWP6,codigoDHEquipoDeMedida,codigoTipoLectura
ES0022000007481662PW1P,2020-05-31,2020-06-16,003,66000,127000,5000,0,0,0,15000,28000,1000,0,0,0,10,10,10,10,10,10"""
    reader = ConsumptionElectricityReader()
    reader.set_credentials("a", "b")
    result = reader._get_by_cup(
        "ES0022000007481662PW1P",
        [
            {
                "cups": "ES0022000007481662PW1P",
                "fechaInicioMesConsumo": "2020-05-31",
                "fechaFinMesConsumo": "2020-06-16",
                "codigoTarifaATR": "003",
                "consumoEnergiaActivaEnWhP1": 66000,
                "consumoEnergiaActivaEnWhP2": 127000,
                "consumoEnergiaActivaEnWhP3": 5000,
                "consumoEnergiaActivaEnWhP4": 0,
                "consumoEnergiaActivaEnWhP5": 0,
                "consumoEnergiaActivaEnWhP6": 0,
                "consumoEnergiaReactivaEnVArhP1": 15000,
                "consumoEnergiaReactivaEnVArhP2": 28000,
                "consumoEnergiaReactivaEnVArhP3": 1000,
                "consumoEnergiaReactivaEnVArhP4": 0,
                "consumoEnergiaReactivaEnVArhP5": 0,
                "consumoEnergiaReactivaEnVArhP6": 0,
                "potenciaDemandadaEnWP1": 10,
                "potenciaDemandadaEnWP2": 10,
                "potenciaDemandadaEnWP3": 10,
                "potenciaDemandadaEnWP4": 10,
                "potenciaDemandadaEnWP5": 10,
                "potenciaDemandadaEnWP6": 10,
                "codigoDHEquipoDeMedida": 10,
                "codigoTipoLectura": 10,
            },
        ],
    )

    assert result.cups == "ES0022000007481662PW1P"
    assert result.start_date == date.fromisoformat("2020-05-31")
    assert result.end_date == date.fromisoformat("2020-06-16")
