"""Support remote proxy — fall back to local when Railway Support is missing."""

from starlette.responses import Response

from app.integration.support_remote import remote_response_is_unavailable


def test_remote_404_not_found_falls_back_to_local():
    resp = Response(content=b'{"detail":"Not Found"}', status_code=404)
    assert remote_response_is_unavailable(resp) is True


def test_remote_thread_not_found_keeps_remote_404():
    resp = Response(content=b'{"detail":"not_found"}', status_code=404)
    assert remote_response_is_unavailable(resp) is False


def test_remote_502_falls_back():
    resp = Response(content=b"bad gateway", status_code=502)
    assert remote_response_is_unavailable(resp) is True


def test_remote_200_keeps_proxy():
    resp = Response(content=b'{"ok":true}', status_code=200)
    assert remote_response_is_unavailable(resp) is False
