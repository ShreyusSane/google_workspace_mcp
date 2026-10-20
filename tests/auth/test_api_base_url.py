"""WORKSPACE_MCP_GOOGLE_API_BASE_URL serves every Google API from another host."""

import pytest
from google.auth.credentials import AnonymousCredentials

from auth.google_auth import build_google_service, get_google_api_base_url

_ENV = "WORKSPACE_MCP_GOOGLE_API_BASE_URL"


def test_unset_or_blank_keeps_google(monkeypatch):
    monkeypatch.delenv(_ENV, raising=False)
    assert get_google_api_base_url() is None
    monkeypatch.setenv(_ENV, "  ")
    assert get_google_api_base_url() is None


def test_adds_trailing_slash(monkeypatch):
    monkeypatch.setenv(_ENV, " http://google-sim:4002 ")
    assert get_google_api_base_url() == "http://google-sim:4002/"


@pytest.mark.parametrize("raw", ["google-sim:4002", "ftp://google-sim", "not a url"])
def test_rejects_values_that_are_not_http_urls(monkeypatch, raw):
    monkeypatch.setenv(_ENV, raw)
    with pytest.raises(ValueError, match=_ENV):
        get_google_api_base_url()


@pytest.mark.parametrize(
    ("service", "version", "default", "overridden"),
    [
        ("gmail", "v1", "https://gmail.googleapis.com/", "http://google-sim:4002/"),
        (
            "calendar",
            "v3",
            "https://www.googleapis.com/calendar/v3/",
            "http://google-sim:4002/calendar/v3/",
        ),
        (
            "drive",
            "v3",
            "https://www.googleapis.com/drive/v3/",
            "http://google-sim:4002/drive/v3/",
        ),
    ],
)
def test_build_keeps_each_api_path_on_the_new_host(
    monkeypatch, service, version, default, overridden
):
    monkeypatch.delenv(_ENV, raising=False)
    assert (
        build_google_service(service, version, AnonymousCredentials())._baseUrl
        == default
    )
    monkeypatch.setenv(_ENV, "http://google-sim:4002")
    assert (
        build_google_service(service, version, AnonymousCredentials())._baseUrl
        == overridden
    )


def test_batch_requests_and_uploads_also_use_the_new_host(monkeypatch):
    monkeypatch.setenv(_ENV, "http://google-sim:4002")
    gmail = build_google_service("gmail", "v1", AnonymousCredentials())
    assert gmail.new_batch_http_request()._batch_uri == "http://google-sim:4002/batch"
    upload = gmail.users().messages().send(userId="me", body={"raw": ""})
    assert upload.uri.startswith("http://google-sim:4002/")
