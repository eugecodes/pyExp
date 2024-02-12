from src.modules.clients.models import Client


def test_client__str__(client: Client):
    assert client.__str__() == "Client: Fiscal name"
