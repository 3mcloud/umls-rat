#!/usr/bin/python
## 6/16/2017 - remove PyQuery dependency
## 5/19/2016 - update to allow for authentication based on api-key, rather than username/pw
## See https://documentation.uts.nlm.nih.gov/rest/authentication.html for full explanation
import functools
import json
import re
from typing import Dict, Iterable

import requests

# from xml.dom.minidom import parseString
# from xml.dom.pulldom import parseString


# from pyquery import PyQuery as pq
# import lxml.html as lh
# from lxml.html import fromstring

uri = "https://utslogin.nlm.nih.gov"
# option 1 - username/pw authentication at /cas/v1/tickets
# auth_endpoint = "/cas/v1/tickets/"
# option 2 - api key authentication at /cas/v1/api-key
auth_endpoint = "/cas/v1/api-key"

_FORM_ACTION_PAT = re.compile(r'<form action="(.+?)" method="POST">')


class Authenticator(object):
    def __init__(self, api_key: str):
        # self.username=username
        # self.password=password
        self.api_key = api_key
        self._auth_svc = "http://umlsks.nlm.nih.gov"
        self._auth_target = self._get_auth_target()

    def _get_auth_target(self):
        # params = {'username': self.username,'password': self.password}
        params = {'apikey': self.api_key}
        h = {"Content-type": "application/x-www-form-urlencoded",
             "Accept": "text/plain", "User-Agent": "python"}
        r = requests.post(uri + auth_endpoint, data=params, headers=h, verify=False)
        if r.status_code != 201:
            raise ValueError(f"Request failed: {r.content}")
        response_text = r.text
        print(response_text)
        # <form action="https://utslogin.nlm.nih.gov/cas/v1/api-key/TGT-909652-QxfVOYJY4vH7J0fdhGtvqbDAdqwnJnYEMg7HHobnUMaFfm7Zir-cas"
        # method="POST">
        match = _FORM_ACTION_PAT.search(response_text)
        result = match.group(1)
        return result

    def get_ticket(self):
        params = {'service': self._auth_svc}
        h = {"Content-type": "application/x-www-form-urlencoded",
             "Accept": "text/plain", "User-Agent": "python"}
        r = requests.post(self._auth_target, data=params, headers=h, verify=False)
        if r.status_code != 200:
            raise ValueError(f"Request failed: {r.content}")
        st = r.text
        return st


_NONE = "NONE"



def result_generator(res: 'Result') -> Iterable['Result']:
    the_result = res._data["result"]
    if "results" in the_result:
        for data in the_result["results"]:
            yield Result(res._auth, data)
    else:
        yield Result(res._auth, the_result)
    pass

class Result(object):
    def __init__(self, auth: Authenticator, data: Dict):
        self._auth = auth
        self._data = data

    def __iter__(self):
        the_result = self._data["result"]
        if "results" in the_result:
            for data in the_result["results"]:
                yield Result(self._auth, data)
        else:
            yield Result(self._auth, the_result)

    @functools.lru_cache()
    def _get_result(self, uri: str) -> 'Result':
        params = {'ticket': self._auth.get_ticket()}
        r = requests.get(uri, params=params, verify=False)
        if r.status_code != 200:
            raise ValueError(f"Request failed: {r.content}")
        return Result(self._auth, r.json())

    def get_value(self, item: str):
        value = self._data.get(item)
        if isinstance(value, str):
            if value.startswith("http"):
                return self._get_result(value)
            elif value == _NONE:
                return None
            else:
                return value
        else:
            return value

    def __getitem__(self, item):
        return self.get_value(item)

    def __str__(self):
        return json.dumps(self._data, indent=2)

    def __repr__(self):
        return str(self)
