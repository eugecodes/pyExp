import pytest

from src.sips.reader import BaseReader, ReaderException, SIPSTypes


def test_base_reader_set_credentials():
    reader = BaseReader()
    reader.set_credentials("a", "b")
    assert reader.consumer_key == "a"
    assert reader.consumer_secret == "b"


def test_base_reader_fetch_no_credentials():
    reader = BaseReader()
    with pytest.raises(ReaderException) as excinfo:
        reader.fetch(SIPSTypes.PS_ELECTRICIDAD, "cups")
        assert excinfo.code == 0
        assert excinfo.message == "Invalid credentials"


def test_base_reader_fetch_invalid_response(mocker):
    request_mock = mocker.patch("src.sips.reader.requests")
    request_mock.get.return_value.status_code = 300
    reader = BaseReader()
    reader.set_credentials("a", "b")
    with pytest.raises(ReaderException) as excinfo:
        reader.fetch(SIPSTypes.PS_ELECTRICIDAD, "cups")
        assert excinfo.code == 300
        assert excinfo.message == "Invalid status response"


def test_base_reader_fetch(mocker):
    request_mock = mocker.patch("src.sips.reader.requests")
    request_mock.get.return_value.status_code = 200
    request_mock.get.return_value.text = "a,b"
    reader = BaseReader()
    reader.set_credentials("a", "b")
    result = reader.fetch(SIPSTypes.PS_ELECTRICIDAD, "cups")
    assert result.fieldnames == ["a", "b"]


def test_base_reader_get(mocker):
    request_mock = mocker.patch("src.sips.reader.requests")
    request_mock.get.return_value.status_code = 200
    request_mock.get.return_value.text = """cups,a,b\n1,2,3"""
    reader = BaseReader()
    reader.set_credentials("a", "b")
    cdv_reader = reader.fetch(SIPSTypes.PS_ELECTRICIDAD, "cups")
    result = BaseReader._get(cdv_reader)
    assert result == {"1": {"a": "2", "b": "3", "cups": "1"}}
