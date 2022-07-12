********
Examples
********

Remember to follow instructions regarding the :ref:`API Key` before running examples. 

:ref:`Core <API MetaThesaurus>`
===============================

.. code-block:: python

   # create an API object
   from umlsrat.api.metathesaurus import MetaThesaurus
   api = MetaThesaurus()



:ref:`Lookup CUI <API Lookup UMLS>`
====================================

Given a concept id from an arbitrary vocabulary, find the corresponding UMLS CUI. 

.. code-block:: python

   # create an API object
   from umlsrat.api.metathesaurus import MetaThesaurus
   api = MetaThesaurus()

   # find CUI for source asserted concept
   from umlsrat.lookup.lookup_umls import get_cuis_for

   # "Cheese" concept in SNOMED
   cheese_cuis = get_cuis_for(api, source_vocab="SNOMEDCT_US", source_ui="102264005")
   # "Fromage" concept in French MeSH
   fromage_cuis = get_cuis_for(api, source_vocab="MSHFRE", source_ui="D002611")

   assert cheese_cuis == fromage_cuis


:ref:`Lookup Definitions <API Lookup Definitions>`
==================================================

Find defined concepts based on description only. 

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


``argparse`` example

.. code-block:: python

   import argparse
   from umlsrat.lookup.lookup_defs import add_args, find_builder
   from umlsrat.util.iterators import definitions_to_md

   parser = argparse.ArgumentParser()
   # add relvant arguments to the parser
   parser = add_args(parser)

   # create an API object
   from umlsrat.api.metathesaurus import MetaThesaurus
   api = MetaThesaurus()

   # normally `cli_args` come from the command line
   cli_args = ["--source-vocab=SNOMEDCT_US"]
   args = parser.parse_args(cli_args)

   # build find function
   find_fn = find_builder(api, args)

   # Find definitions for each of the following SNOMED concepts
   for ui in ["73539009", "242593005", "261188006"]:
      concepts = find_fn(source_ui=ui, broader=True)
      print(definitions_to_md(concepts))
      print("_" * 40)


Scripts
=======

.. toctree::
   :maxdepth: 2

   script_examples/definitions
