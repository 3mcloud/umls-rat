UMLS RAT
=========

.. image:: https://readthedocs.org/projects/urls-rat/badge/?version=latest
    :target: https://urls-rat.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://github.com/3mcloud/umls-rat/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/3mcloud/umls-rat/actions/workflows/python-package.yml 


UMLS RAT (**R**\ EST **A**\ PI **T**\ ool) provides a reasonable interface to the `UMLS Metathesaurus <https://uts.nlm.nih.gov/uts/umls/home>`_ via the `REST API <https://documentation.uts.nlm.nih.gov/rest/home.html>`__. We cache responses using `requests cache <https://requests-cache.readthedocs.io/en/stable/>`__ to speed things up. Ultimately, you will only end up downloading as much data as you *need* which for most use cases is a relatively small portion of the whole. If you need the entire Metathesaurus, this is not the best tool.

Install
-------

.. code-block:: console
    
    pip install umls-rat

.. _API Key:

API Key
=======

Before you get started, you first need to `get an API key from UMLS <https://uts.nlm.nih.gov/uts/signup-login>`__. This key is passed to the :py:class:`umlsrat.api.metathesaurus.MetaThesaurus` constructor. Perhaps easier, set the ``UMLS_API_KEY`` environment variable which is read when no key is passed. 


SSL
===

Note that you may need to add an SSL certificate which can be done by setting the ``REQUESTS_CA_BUNDLE`` environment variable. `See here for more info <https://requests.readthedocs.io/en/master/user/advanced/#ssl-cert-verification>`__. 


Development
===========

Install requirements. 

.. code-block:: console

    pip install -r requirements.txt

Execute unit tests. Set ``UMLS_API_KEY`` or pass in with ``--api-key`` arg.

.. code-block:: console

    PYTHONPATH=. pytest -vs tests

Cached requests are stored in ``~/.cache/umls-rat``. Caching can be disabled when running the tests, with the ``--no-cache`` flag, eg

.. code-block:: console

    PYTHONPATH=. pytest -vs tests --cache=False


The default version of UMLS used is a constant :const:`umlsrat.const.DEFAULT_UMLS_VERSION`. The version used for testing can be modified at runtime with the ``--umls-version`` arg, eg

.. code-block:: console

    PYTHONPATH=. pytest -vs tests --cache=False --umls-version current


Links
=====

* `Source on Github <https://github.mmm.com/OneNLU/umls-rat>`_.
* `Latest documentation <https://urls-rat.readthedocs.io/en/latest/>`_.
