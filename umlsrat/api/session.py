import logging
import os
from os.path import expanduser
from typing import Optional, Any, Dict, List

from ratelimit import sleep_and_retry, limits
from requests import Session, HTTPError, Response
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3 import Retry

from umlsrat import const


def _set_retries(session):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _configure_session(session):
    _set_retries(session)
    return session


def _cache_path(cache_name: str) -> str:
    return expanduser(f"~/.cache/umls-rat/{cache_name}")


_NONE = "NONE"


def _interpret_none(value: Any):
    if isinstance(value, str):
        if value == _NONE:
            return None
        else:
            return value
    elif isinstance(value, Dict):
        return {key: _interpret_none(value) for key, value in value.items()}
    elif isinstance(value, List):
        return [_interpret_none(_) for _ in value]
    else:
        return value


class MetaThesaurusSession(object):
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Constructor.

        If ``api_key`` is not passed, the value will be read from the ``UMLS_API_KEY`` environment variable.

        :param api_key: API key acquired from `here <https://uts.nlm.nih.gov/uts/signup-login>`__
        :param use_cache: use cache for requests (default ``True``)
        """
        if api_key:
            self._api_key = api_key
        else:
            self._api_key = os.environ.get(const.API_KEY_ENV_VAR)
            if not self._api_key:
                raise KeyError(
                    f"`api_key` not passed and `{const.API_KEY_ENV_VAR}` not set."
                )

        self.use_cache = use_cache

        if self.use_cache:
            self.session = CachedSession(
                cache_name=_cache_path("api-cache"),
                ignored_parameters=["apiKey"],
                allowable_codes=[200, 400, 404],
            )
        else:
            self.session = Session()

        _configure_session(self.session)

    @property
    def _logger(self):
        return logging.getLogger(self.__class__.__name__)

    def _get_cached(self, url: str, params) -> Optional[Response]:
        """Get the cached response or None"""
        if not self.use_cache:
            return None

        response = self.session.get(url, params=params, only_if_cached=True)
        if response.status_code != 504:
            return response
        else:
            return None

    @sleep_and_retry
    @limits(calls=20, period=1)
    def _get_http(self, url, params):
        """
        Rate limited per `Terms of Service <https://documentation.uts.nlm.nih.gov/terms-of-service.html>`__
        """
        response = self.session.get(url=url, params=params)
        return response

    def get(self, url: str, strict: Optional[bool] = False, **params) -> Optional[Dict]:
        assert url, "Must provide URL"

        if "apiKey" in params:
            self._logger.warning(
                f"'apiKey' should not be in params! Will be overwritten..."
            )

        params["apiKey"] = self._api_key
        try:
            response = self._get_cached(url, params=params)
            if response is None:
                response = self._get_http(url, params=params)
        except Exception as e:
            self._logger.exception("Failed to get %s", url)
            raise e

        try:
            response.raise_for_status()
        except HTTPError as e:
            if strict:
                raise e

            self._logger.debug("Caught HTTPError: %s", e)
            if e.response.status_code == 400 or e.response.status_code == 404:
                # we interpret this as "you're looking for something that isn't there"
                return None
            else:
                raise e

        return _interpret_none(response.json())
