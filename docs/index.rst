.. UMLS RAT documentation master file, created by
   sphinx-quickstart on Thu May 19 11:51:06 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to UMLS RAT's documentation!
====================================

.. include:: intro.rst

.. _API Key:

API Key
=======

 Before you get started, you first need to `get an API key from UMLS <https://uts.nlm.nih.gov/uts/signup-login>`__. By default, your API key will be read from the environment variable ``UMLS_API_KEY``. If this variable is not set, you must pass your key to the :py:class:`umlsrat.api.rat_session.MetaThesaurusSession` constructor.

SSL
===

Note that you may need to add an SSL certificate which can be done by setting the ``REQUESTS_CA_BUNDLE`` environment variable. `See here for more info <https://requests.readthedocs.io/en/master/user/advanced/#ssl-cert-verification>`__. 


Development
===========

Install poetry environment. 

.. code-block:: console

    poetry install

Execute unit tests. Set ``UMLS_API_KEY`` or pass in with ``--api-key`` arg.

.. code-block:: console

    poetry run python -m pytest -sv tests

Cached requests are stored in ``~/.cache/umls-rat``. Caching can be disabled when running the tests, with the ``--no-cache`` flag, eg

.. code-block:: console

    poetry run python -m pytest -sv tests --cache=False


The default version of UMLS used is a constant :const:`umlsrat.const.DEFAULT_UMLS_VERSION`. The version used for testing can be modified at runtime with the ``--umls-version`` arg, eg

.. code-block:: console

    poetry run python -m pytest -sv tests --cache=False --umls-version current


.. toctree::
   :maxdepth: 2

   api
   examples
   umls-info

.. include:: links.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
