********
API Docs
********

.. _API MetaThesaurus:

MetaThesaurus
=============

This object provides access to the basic functions of the UMLS Metathesaurus REST API. 

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus
   umlsrat.api.metathesaurus.MetaThesaurus.add_args

.. rubric:: UMLS Concepts

.. autosummary::
   :nosignatures:
   :recursive:

   umlsrat.api.metathesaurus.MetaThesaurus.get_concept
   umlsrat.api.metathesaurus.MetaThesaurus.get_definitions
   umlsrat.api.metathesaurus.MetaThesaurus.get_relations
   umlsrat.api.metathesaurus.MetaThesaurus.get_atoms_for_cui
   umlsrat.api.metathesaurus.MetaThesaurus.get_atom

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
   umlsrat.api.metathesaurus.MetaThesaurus.crosswalk

.. _API Lookup:

Lookup
======

This is a collection of utilty functions for searching ontologies for desired concepts. 


.. _API Lookup Definitions:

Definitions
-----------

Functions for finding defined concepts. 

.. autosummary::
   :nosignatures:

   umlsrat.lookup.lookup_defs.definitions_bfs
   umlsrat.lookup.lookup_defs.find_defined_concepts
   umlsrat.lookup.lookup_defs.find_builder
   umlsrat.lookup.lookup_defs.add_args

.. _API Lookup Descriptions:

Descriptions
------------

Find descriptions for a concept; i.e. find all possible names for a given concept. 

.. autosummary::
   :nosignatures:

   umlsrat.lookup.lookup_desc.get_synonyms
   umlsrat.lookup.lookup_desc.find_synonyms

.. _API Lookup UMLS:

UMLS
----

Functions which find UMLS concepts and CUIs

.. autosummary::
   :nosignatures:
   :recursive:
   
   umlsrat.lookup.lookup_umls.get_cuis_for
   umlsrat.lookup.lookup_umls.get_related_cuis
   umlsrat.lookup.lookup_umls.get_broader_cuis
   umlsrat.lookup.lookup_umls.get_narrower_cuis
   umlsrat.lookup.lookup_umls.term_search
   

Signatures
==========

All method signatures are found here.

.. rubric:: MetaThesaurus

.. automodule:: umlsrat.api.metathesaurus
   :members:

.. rubric:: Definitions

.. automodule:: umlsrat.lookup.lookup_defs
    :members: 

.. rubric:: Descriptions

.. automodule:: umlsrat.lookup.lookup_desc
    :members: 

.. rubric:: UMLS

.. automodule:: umlsrat.lookup.lookup_umls
    :members: 
