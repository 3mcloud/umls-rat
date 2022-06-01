UMLS RAT
=========

UMLS RAT (**R**\ EST **A**\ PI **T**\ ool) provides a reasonable interface to the `UMLS Metathesaurus <https://uts.nlm.nih.gov/uts/umls/home>`_ via the `REST API <https://documentation.uts.nlm.nih.gov/rest/home.html>`_. We cache responses using `requests cache <https://requests-cache.readthedocs.io/en/stable/>`_ to speed things up. Ultimately, you should only end up downloading as much data as you *need*. If you need the entirety of UMLS or one of the contained vocabularies, this is not the best tool.

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

Execute unit tests with your API key. 

.. code-block:: console

    PYTHONPATH=. pytest -vs tests --api-key=${UMLS_API_KEY}

Cached requests are stored in ``~/.cache/umls-rat``. Caching can be disabled when running the tests, with the ``--no-cache`` flag, eg

.. code-block:: console

    PYTHONPATH=. pytest -vs tests --api-key=${UMLS_API_KEY} --no-cache


The default version of UMLS used is a constant :const:`umlsrat.const.DEFAULT_UMLS_VERSION`. The version used for testing can be modified at runtime with the ``--umls-version`` arg, eg

.. code-block:: console

    PYTHONPATH=. pytest -vs tests --api-key=${UMLS_API_KEY} --no-cache --umls-version current


Links
=====

* `Source on Github <https://github.mmm.com/OneNLU/umls-rat>`_.
* `Latest documentation <https://jenkins.firebird.mmm.com/job/MMODAL/job/NLU-ML-Libraries/job/umls-rat/job/main/Documentation/index.html#>`_.
