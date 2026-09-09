import pytest
from unittest.mock import Mock

from deezer_analytics.deezer_client import DeezerClient, DeezerAPIError


def test_build_url():
    with DeezerClient() as client:
        assert client._build_url("/track/123") == (
            "https://api.deezer.com/track/123"
        )
        assert client._build_url("track/123") == (
            "https://api.deezer.com/track/123"
        )


def test_get_success():
    with DeezerClient() as client:
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "id": 123,
            "title": "Test",
        }

        client._session.get = Mock(return_value=response)

        result = client.get("/track/123")

        assert result == {
            "id": 123,
            "title": "Test",
        }

        client._session.get.assert_called_once()


def test_get_http_error():
    with DeezerClient() as client:
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.reason = "Internal Server Error"
        response.json.return_value = {
            "error": {
                "message": "Server error",
            }
        }

        client._session.get = Mock(return_value=response)

        with pytest.raises(
            DeezerAPIError,
            match="Server error",
        ):
            client.get("/track/123")


def test_get_deezer_error():
    with DeezerClient() as client:
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "error": {
                "code": 800,
                "message": "no data",
            }
        }

        client._session.get = Mock(return_value=response)

        with pytest.raises(
            DeezerAPIError,
            match="no data",
        ):
            client.get("/track/123")


def test_get_invalid_json():
    with DeezerClient() as client:
        response = Mock()
        response.ok = True
        response.json.side_effect = ValueError

        client._session.get = Mock(return_value=response)

        with pytest.raises(
            DeezerAPIError,
            match="JSON valide",
        ):
            client.get("/track/123")
