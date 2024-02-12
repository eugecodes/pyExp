import csv
from enum import Enum
from io import StringIO
from typing import Dict, List

import requests
from requests_oauthlib import OAuth1
from starlette.status import HTTP_200_OK


class SIPSTypes(Enum):
    PS_ELECTRICIDAD = "SIPS2_PS_ELECTRICIDAD"
    CONSUMOS_ELECTRICIDAD = "SIPS2_CONSUMOS_ELECTRICIDAD"
    PS_GAS = "SIPS2_PS_GAS"
    CONSUMOS_GAS = "SIPS2_CONSUMOS_GAS"


class ReaderException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.code, self.message)


class BaseReader:
    FIELDS = []

    BASE_URL = "https://api.cnmc.gob.es/verticales/v1/SIPS/consulta/v1/"
    consumer_key = None
    consumer_secret = None

    def set_credentials(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def fetch(self, sips_type: SIPSTypes, cups: List[str]):
        if self.consumer_key is None or self.consumer_secret is None:
            raise ReaderException(code=0, message="Invalid credentials")
        params = {"cups": ",".join(cups)}
        oauth = OAuth1(self.consumer_key, client_secret=self.consumer_secret)

        headers = {
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/111.0.0.0 Safari/537.36",
        }

        r = requests.get(
            f"{self.BASE_URL}{sips_type.value}.csv",
            auth=oauth,
            params=params,
            headers=headers,
        )
        if r.status_code != HTTP_200_OK:
            raise ReaderException(code=r.status_code, message="Invalid status response")

        f = StringIO(r.text)
        reader = csv.DictReader(f, delimiter=",")

        return reader

    @staticmethod
    def _get(result: csv.DictReader) -> Dict:
        data = dict()
        for row in result:
            data[row["cups"]] = row

        return data
