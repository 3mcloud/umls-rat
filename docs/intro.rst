UMLS RAT (**R**\ EST **A**\ PI **T**\ ool) provides a reasonable interface to the `UMLS Metathesaurus <https://uts.nlm.nih.gov/uts/umls/home>`_ via the `REST API <https://documentation.uts.nlm.nih.gov/rest/home.html>`__. We cache responses using `requests cache <https://requests-cache.readthedocs.io/en/stable/>`__ to speed things up. Ultimately, you will only end up downloading as much data as you *need* which for most use cases is a relatively small portion of the whole. If you need the entire Metathesaurus, this is not the best tool.

Install
-------

.. code-block:: console
    
    pip install umls-rat
