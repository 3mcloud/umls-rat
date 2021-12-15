import functools
import os
from datetime import timedelta
from os.path import expanduser

from requests import Session
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3 import Retry

_this_dir = os.path.dirname(os.path.normpath(__file__))
_pem_file_path = os.path.join(_this_dir, "tls-ca-bundle.pem")


def _configure_session(session):
    session.verify = _pem_file_path
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def _cache_path(cache_name: str) -> str:
    return expanduser(f"~/.cache/umls-rat/{cache_name}")


@functools.lru_cache(maxsize=1)
def api_session() -> CachedSession:
    session = CachedSession(
        cache_name=_cache_path("api-cache"),
        ignored_parameters=["ticket"],
    )
    return _configure_session(session)


@functools.lru_cache(maxsize=1)
def tgt_session() -> CachedSession:
    """Get a Ticket-Granting Ticket (TGT). The TGT is valid for 8 hours."""
    session = CachedSession(
        cache_name=_cache_path("tgt-cache"),
        allowable_methods=["POST"],
        expire_after=timedelta(hours=8),
    )
    return _configure_session(session)


@functools.lru_cache(maxsize=1)
def uncached_session() -> Session:
    return _configure_session(Session())
