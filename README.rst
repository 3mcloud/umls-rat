UMLS RAT
=========

UMLS RAT (**R**\ EST **A**\ PI **T**\ ool) provides a reasonable interface to the `UMLS Metathesaurus <https://uts.nlm.nih.gov/uts/umls/home>`_ via the `REST API <https://documentation.uts.nlm.nih.gov/rest/home.html>`_. We cache responses using `requests cache <https://requests-cache.readthedocs.io/en/stable/>`_ to speed things up. Ultimately, you should only end up downloading as much data as you *need*. If you need the entirety of UMLS or one of the contained vocabularies, this is not the best tool.

Install
-------

.. code-block:: console
    
    pip install umls-rat

Usage
-----

Included is one sample entry point ``definitions-dump.py``. Examles can be found here :ref:`Examples/Definitions`

Links
-----

* `Source on Github <https://github.mmm.com/OneNLU/umls-rat>`_.
* `Latest documentation <https://jenkins.firebird.mmm.com/job/MMODAL/job/NLU-ML-Libraries/job/umls-rat/job/main/Documentation/index.html#>`_.
