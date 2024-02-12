from config.settings import settings
from src.modules.saving_studies.models import SavingStudy
from src.sips.consumption_electricity import ConsumptionElectricityReader
from src.sips.ps_electricity import PsElectricityReader


def fill_study_with_sips(saving_study: SavingStudy) -> SavingStudy:
    reader = PsElectricityReader()
    reader.set_credentials(settings.SIPS_CONSUMER_KEY, settings.SIPS_CONSUMER_SECRET)
    data = reader.get([saving_study.cups])

    for cups, item in data.items():
        saving_study.power_1 = int(item["potenciasContratadasEnWP1"]) / 1000
        saving_study.power_2 = int(item["potenciasContratadasEnWP2"]) / 1000
        saving_study.power_3 = int(item["potenciasContratadasEnWP3"]) / 1000
        saving_study.power_4 = int(item["potenciasContratadasEnWP4"]) / 1000
        saving_study.power_5 = int(item["potenciasContratadasEnWP5"]) / 1000
        saving_study.power_6 = int(item["potenciasContratadasEnWP6"]) / 1000

    reader = ConsumptionElectricityReader()
    reader.set_credentials(settings.SIPS_CONSUMER_KEY, settings.SIPS_CONSUMER_SECRET)
    data = reader.get([saving_study.cups])

    for cups, item in data.items():
        saving_study.consumption_p1 = item.consumption_p1
        saving_study.consumption_p2 = item.consumption_p2
        saving_study.consumption_p3 = item.consumption_p3
        saving_study.consumption_p4 = item.consumption_p4
        saving_study.consumption_p5 = item.consumption_p5
        saving_study.consumption_p6 = item.consumption_p6
        saving_study.annual_consumption = item.annual_consumption
        saving_study.analyzed_days = item.analyzed_days

    return saving_study
