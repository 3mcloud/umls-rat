import pytest

from umlsrat import const
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.api.session import MetaThesaurusSession


def pytest_addoption(parser):
    parser.addoption("--api-key", type=str, help="API key", default=None)
    parser.addoption("--no-cache", help="Do not use cache", action="store_true")
    parser.addoption(
        "--umls-version",
        type=str,
        help="UMLS version",
        default=const.DEFAULT_UMLS_VERSION,
    )


@pytest.fixture(scope="session")
def _no_cache(request):
    return request.config.option.no_cache


@pytest.fixture(scope="session")
def _umls_version(request):
    return request.config.option.umls_version


@pytest.fixture(scope="session")
def _api_key(request):
    return request.config.option.api_key


@pytest.fixture(scope="session")
def mt_session(_api_key, _no_cache):
    return MetaThesaurusSession(api_key=_api_key, use_cache=not _no_cache)


@pytest.fixture(scope="session")
def api(mt_session, _umls_version):
    return MetaThesaurus(session=mt_session, version=_umls_version)
