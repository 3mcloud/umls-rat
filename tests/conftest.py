import pytest

from umlsrat import const
from umlsrat.api.metathesaurus import MetaThesaurus


def pytest_addoption(parser):
    parser.addoption(
        "--api-key",
        type=str,
        help="API key",
        required=True,
    )
    parser.addoption("--no-cache", help="Do not use cache", action="store_true")
    parser.addoption(
        "--umls-version",
        type=str,
        help="UMLS version",
        default=const.DEFAULT_UMLS_VERSION,
    )


@pytest.fixture(scope="session")
def _no_cache(request):
    value = request.config.option.no_cache
    if value is None:
        pytest.skip()
        return None

    return value


@pytest.fixture(scope="session")
def _umls_version(request):
    value = request.config.option.umls_version
    if value is None:
        pytest.skip()
        return None

    return value


@pytest.fixture(scope="session")
def api_key(request):
    api_key = request.config.option.api_key
    if api_key is None:
        pytest.skip()
        return None

    return api_key


@pytest.fixture(scope="session")
def api(api_key, _no_cache, _umls_version):
    return MetaThesaurus(api_key, version=_umls_version, use_cache=not _no_cache)
