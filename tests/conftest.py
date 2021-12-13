import pytest

from umlsrat.api.metathesaurus import MetaThesaurus


def pytest_addoption(parser):
    parser.addoption(
        "--api-key",
        type=str,
        help="API key",
        required=True,
    )


@pytest.fixture(scope="session")
def api(request):
    api_key = request.config.option.api_key
    if api_key is None:
        pytest.skip()
        return None

    return MetaThesaurus(api_key)
