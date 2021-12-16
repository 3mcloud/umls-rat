import functools
import os
from datetime import timedelta
from os.path import expanduser

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3 import Retry

_this_dir = os.path.dirname(os.path.normpath(__file__))
_pem_file_path = os.path.join(_this_dir, "tls-ca-bundle.pem")


def _set_verify(session):
    session.verify = _pem_file_path
    return session


def _set_retries(session):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def _configure_session(session):
    _set_verify(session)
    _set_retries(session)
    return session


def _cache_path(cache_name: str) -> str:
    return expanduser(f"~/.cache/umls-rat/{cache_name}")


def check_cache(session: CachedSession, method: str, url: str, **params):
    request = requests.Request(method=method, url=url, params=params)
    request = session.prepare_request(request)

    # verify needs to be added here for some reason
    add_verify = {"verify": _pem_file_path, **params}
    key = session.cache.create_key(request, **add_verify)
    value = session.cache.get_response(key)
    return value


@functools.lru_cache(maxsize=1)
def api_session() -> CachedSession:
    session = CachedSession(
        cache_name=_cache_path("api-cache"),
        ignored_parameters=["ticket"],
        allowable_codes=[200, 400],
    )
    return _configure_session(session)


@functools.lru_cache(maxsize=1)
def tgt_session() -> CachedSession:
    """Get a Ticket-Granting Ticket (TGT). The TGT is valid for 8 hours."""
    # expire the cache after 7 hours just to be safe?
    session = CachedSession(
        cache_name=_cache_path("tgt-cache"),
        allowable_methods=["POST"],
        expire_after=timedelta(hours=7),
    )
    return _configure_session(session)


@functools.lru_cache(maxsize=1)
def uncached_session() -> Session:
    return _configure_session(Session())
