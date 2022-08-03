import argparse
import json
import logging
import os
from os.path import expanduser
from typing import Optional, Any, Dict, List, Iterator

from backoff import on_exception, expo
from ratelimit import limits, RateLimitException
from requests import Session, HTTPError, Response
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3 import Retry

from umlsrat import const
from umlsrat.util import args_util


def _set_retries(session):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
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


def _extract_results(response_json: Dict) -> List[Dict]:
    """
    Extract results from response json.
    :param response_json:
    :return: list of results or None if invalid
    """
    if not response_json:
        return []

    result = response_json["result"]

    if "results" in result:
        return result["results"]
    else:
        return result


class MetaThesaurusSession(object):
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Constructor.

        If ``api_key`` is not passed, the value will be read from the ``UMLS_API_KEY`` environment variable.

        :param api_key: API key acquired from `here <https://uts.nlm.nih.gov/uts/signup-login>`__. If not passed as an argument, the value will be read from the ``UMLS_API_KEY`` environment variable.
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

        self.session = _configure_session(self.session)

    @staticmethod
    def add_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Add constructor arguments to parser.

        :param parser: parser
        :return: the same parser
        """
        group = parser.add_argument_group("Session")
        group.add_argument("--api-key", type=str, help="API key", default=None)
        group.add_argument(
            "--use-cache",
            help="Controls whether or not we use the response cache",
            type=args_util.str2bool,
            default=True,
        )

        return parser

    @staticmethod
    def from_namespace(args: argparse.Namespace) -> "MetaThesaurusSession":
        """
        Construct new object using values from namespace.

        :param args: parsed args
        :return: new session
        """
        return MetaThesaurusSession(api_key=args.api_key, use_cache=args.use_cache)

    @property
    def _logger(self):
        return logging.getLogger(self.__class__.__name__)

    def _get_cached(self, url: str, params) -> Optional[Response]:
        """Get the cached response or None"""
        if not self.use_cache:
            return None

        response = self.session.get(url, params=params, only_if_cached=True)
        if response.status_code == 504:
            return None
        else:
            return response

    @on_exception(expo, RateLimitException, max_tries=8)
    @limits(calls=20, period=1)
    def _get_http(self, url, params):
        """
        Rate limited per `Terms of Service <https://documentation.uts.nlm.nih.gov/terms-of-service.html>`__
        """
        response = self.session.get(url=url, params=params)
        return response

    def get_json(
        self, url: str, strict: Optional[bool] = False, **params
    ) -> Optional[Dict]:
        """
        Get JSON response and interpret None values.

        :param url: target URL
        :param strict: if True raise for status even when expected
        :param params: params to the get call. params with None value are dropped.
        :return: the JSON response
        """
        assert url, "Must provide URL"

        if "apiKey" in params:
            self._logger.warning(
                f"'apiKey' should not be in params! Will be overwritten..."
            )

        # copy and drop None values
        params = {k: v for k, v in params.items() if v is not None}
        # add apiKey
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

    def get_results(
        self,
        url: str,
        max_results: Optional[int] = None,
        **params,
    ) -> Iterator[Dict]:
        """
        Get data from arbitrary URI. Will return an empty list on 400 or 404
        unless `strict=True` is in kwargs, in which case it will raise.

        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param max_results: maximum number of result to return. None = no max
        :param params: parameters sent with the get request
        :return: generator yielding results
        """
        assert url
        if max_results is not None:
            assert max_results > 0, "max_results must be > 0"

        response_json = self.get_json(url, **params)
        if not response_json:
            return

        # get page count from first call
        page_count = response_json.get("pageCount", None)

        if "pageNumber" not in response_json:
            raise ValueError(
                "Expected pagination fields in response:\n"
                "{}".format(json.dumps(response_json, indent=2))
            )

        if "pageNumber" not in params:
            params["pageNumber"] = 1
        else:
            self._logger.warning(
                "Starting pagination from page %d", params["pageNumber"]
            )

        n_yielded = 0
        while True:
            results = _extract_results(response_json)
            if not results:
                return

            for r in results:
                yield r
                n_yielded += 1
                if n_yielded == max_results:
                    return

            if page_count == params["pageNumber"]:
                # no more pages
                return

            # next page
            params = dict(pageNumber=params.pop("pageNumber") + 1, **params)
            response_json = self.get_json(url, **params)

    def get_single_result(self, url: str, **params) -> Optional[Dict]:
        """
        When you know there will only be one coming back

        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param params: parameters sent with the get request
        :return: a result or None
        """
        response_json = self.get_json(url, **params)
        if not response_json:
            return

        return response_json["result"]
