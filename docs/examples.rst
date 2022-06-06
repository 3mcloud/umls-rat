Examples
========

Remember to follow instructions regarding the :ref:`API Key` before running examples. 

.. rubric:: Find UMLS CUI

.. code-block:: python

   # create an API object
   from umlsrat.api.metathesaurus import MetaThesaurus
   api = MetaThesaurus()

   # find CUI for source asserted concept
   from umlsrat.lookup.lookup_umls import get_cuis_for

   cheese_cuis = get_cuis_for(api, source_vocab="SNOMEDCT_US", source_ui="102264005")

   fromage_cuis = get_cuis_for(api, source_vocab="MSHFRE", source_ui="D002611")

   assert cheese_cuis == fromage_cuis

.. rubric:: Find Definitions

.. code-block:: python

   # create an API object
   from umlsrat.api.metathesaurus import MetaThesaurus
   api = MetaThesaurus()

   # find defined concepts for "aortic aneurysm"
   from umlsrat.lookup.lookup_defs import find_defined_concepts
   aa_concepts = find_defined_concepts(api, source_desc="aortic aneurysm")

   # pull out definitions
   from umlsrat.util.iterators import extract_definitions
   aa_definitions = extract_definitions(aa_concepts)

   print(aa_definitions)

.. rubric:: Scripts

.. toctree::
   :maxdepth: 2

   examples/definitions
