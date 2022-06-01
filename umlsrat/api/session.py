import functools
from os.path import expanduser

from requests import Session
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3 import Retry


def _set_retries(session):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _configure_session(session):
    _set_retries(session)
    return session


def _cache_path(cache_name: str) -> str:
    return expanduser(f"~/.cache/umls-rat/{cache_name}")


@functools.lru_cache(maxsize=1)
def api_session() -> CachedSession:
    """
    Get session for API calls.
    :return: session
    """
    session = CachedSession(
        cache_name=_cache_path("api-cache"),
        ignored_parameters=["apiKey"],
        allowable_codes=[200, 400, 404],
    )
    return _configure_session(session)


@functools.lru_cache(maxsize=1)
def uncached_session() -> Session:
    """
    Get a session without caching
    :return: session
    """
    return _configure_session(Session())
