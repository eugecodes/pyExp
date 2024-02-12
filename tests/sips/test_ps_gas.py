# def test_ps_gas_reader_get(mocker):
#     request_mock = mocker.patch("src.sips.reader.requests")
#     request_mock.get.return_value.status_code = 200
#     request_mock.get.return_value.text = """cups,a,b\n1,2,3"""
#     reader = PsGasReader()
#     reader.set_credentials("a", "b")
#     result = reader.get(["cups"])
#     assert result == {"1": {"a": "2", "b": "3", "cups": "1"}}
