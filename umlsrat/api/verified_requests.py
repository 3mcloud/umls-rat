import os

import requests

_this_dir = os.path.dirname(os.path.normpath(__file__))
_pem_file_path = os.path.join(_this_dir, "tls-ca-bundle.pem")


def _add_verify(kwargs):
    kwargs["verify"] = _pem_file_path


def post(*args, **kwargs) -> requests.Response:
    _add_verify(kwargs)
    return requests.post(*args, **kwargs)


def get(*args, **kwargs) -> requests.Response:
    _add_verify(kwargs)
    return requests.get(*args, **kwargs)
