#!/usr/bin/python
## 6/16/2017 - remove PyQuery dependency
## 5/19/2016 - update to allow for authentication based on api-key, rather than username/pw
## See https://documentation.uts.nlm.nih.gov/rest/authentication.html for full explanation
import re

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
