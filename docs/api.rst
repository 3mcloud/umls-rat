API Docs
========

MetaThesaurus
-------------

This object provides access to the basic functions of the UMLS REST API. 

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus

.. rubric:: UMLS Concepts

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus.get_concept
   umlsrat.api.metathesaurus.MetaThesaurus.get_definitions
   umlsrat.api.metathesaurus.MetaThesaurus.get_relations
   umlsrat.api.metathesaurus.MetaThesaurus.get_ancestors
   umlsrat.api.metathesaurus.MetaThesaurus.get_atoms

.. rubric:: Search

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus.search

.. rubric:: Source Asserted Concepts

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus.get_source_concept
   umlsrat.api.metathesaurus.MetaThesaurus.get_source_relations
   umlsrat.api.metathesaurus.MetaThesaurus.get_source_parents
   umlsrat.api.metathesaurus.MetaThesaurus.get_source_ancestors


Lookup
------

This is a collection of utilty functions for searching ontologies for desired concepts. 


.. rubric:: Definitions

Functions for finding definitions of concepts. 

.. autosummary::
   :nosignatures:

   umlsrat.lookup.definitions.find_defined_concepts
   umlsrat.lookup.definitions.broader_definitions_bfs

.. rubric:: UMLS

Functions which find UMLS concepts and CUIs

.. autosummary::
   :nosignatures:
   :recursive:
   
   umlsrat.lookup.umls


Signatures
----------

All method signatures are found here.

.. rubric:: MetaThesaurus

.. automodule:: umlsrat.api.metathesaurus
   :members:

.. rubric:: Definitions

.. automodule:: umlsrat.lookup.definitions
    :members: 

.. rubric:: UMLS

.. automodule:: umlsrat.lookup.umls
    :members: 
