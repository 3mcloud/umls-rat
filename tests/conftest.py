import logging
import random

import pytest

from umlsrat import const
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.api.rat_session import MetaThesaurusSession
from umlsrat.util import args_util

logging.basicConfig(level=logging.WARNING)


def pytest_addoption(parser):
    parser.addoption("--api-key", type=str, help="API key", default=None)
    parser.addoption(
        "--use-cache", help="use cache", type=args_util.str2bool, default=True
    )
    parser.addoption(
        "--umls-version",
        type=str,
        help="UMLS version",
        default=const.DEFAULT_UMLS_VERSION,
    )


@pytest.fixture(scope="session")
def mt_session(request):
    return MetaThesaurusSession(
        api_key=request.config.option.api_key,
        use_cache=request.config.option.use_cache,
    )


@pytest.fixture(scope="session")
def api(request, mt_session):
    return MetaThesaurus(
        session=mt_session, umls_version=request.config.option.umls_version
    )


@pytest.fixture(scope="session")
def rng() -> random.Random:
    return random.Random(8374927)
