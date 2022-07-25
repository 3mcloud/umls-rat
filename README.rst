UMLS RAT
=========

.. image:: https://readthedocs.org/projects/urls-rat/badge/?version=latest
    :target: https://urls-rat.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://github.com/3mcloud/umls-rat/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/3mcloud/umls-rat/actions/workflows/python-package.yml 
.. image:: https://badge.fury.io/py/umls-rat.svg
   :target: https://pypi.python.org/pypi/umls-rat/
..
    Includes don't work with GitHub https://github.com/github/markup/issues/172
    docs/intro.rst

UMLS RAT (**R**\ EST **A**\ PI **T**\ ool) provides a reasonable interface to the `UMLS Metathesaurus <https://uts.nlm.nih.gov/uts/umls/home>`_ via the `REST API <https://documentation.uts.nlm.nih.gov/rest/home.html>`__. We cache responses using `requests cache <https://requests-cache.readthedocs.io/en/stable/>`__ to speed things up. Ultimately, you will only end up downloading as much data as you *need* which for most use cases is a relatively small portion of the whole. If you need the entire Metathesaurus, this is not the best tool.

Install
-------

.. code-block:: console
    
    pip install umls-rat

..
    docs/links.rst

Links
=====

* `Latest documentation <https://urls-rat.readthedocs.io/en/latest/>`_.
* `Source on Github <https://github.com/3mcloud/umls-rat>`_.
