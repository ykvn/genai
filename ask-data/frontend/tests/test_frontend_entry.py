import pytest

from frontend_entry import _coerce_backend_payload


class DummyResponse:
    def __init__(self, text="", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        raise ValueError("No JSON object could be decoded")


def test_coerce_backend_payload_returns_text_for_empty_body():
    response = DummyResponse(text="")

    payload, error = _coerce_backend_payload(response)

    assert payload is None
    assert "empty response body" in error.lower()


def test_coerce_backend_payload_returns_text_for_html_response():
    response = DummyResponse(text="<html>bad gateway</html>", status_code=502)

    payload, error = _coerce_backend_payload(response)

    assert payload is None
    assert "502" in error
    assert "bad gateway" in error.lower()
