.. highlight:: markdown

Definitions Dump
================

The script `definitions-dump.py` will do a search for concepts with definitions, starting from the one specified at the CLI. The full data for those concepts is written to a ``JSON`` file under ``definitions/`` as well as *just* the definitions written as MarkDown.

Get definitions for this out-dated "back" concept: `450807008`

.. code-block:: console

    python definitions-dump.py --concept-id=450807008 --source-vocab=SNOMEDCT_US


::

    Back structure, including back of neck
    ======================================
    1. subdivision of body proper, each instance of which has as its
    direct parts some back of neck and some back of trunk. Examples: There
    is only one back of body proper.


Now get one in Spanish

.. code-block:: console

    python definitions-dump.py --concept-id=450807008 --source-vocab=SNOMEDCT_US --language=SPA


::

    Body Regions
    ============
    1. Áreas anatómicas del cuerpo.


Look for a concept using the description only

.. code-block:: console

    python definitions-dump.py --source-desc="Physical therapy" --language=SPA

::

    Rehabilitation therapy
    ======================
    1. Recuperación de las funciones humanas, al mayor grado posible, en
    una perosna o personas que padecen enfermedad o lesión.

    Therapeutic procedure
    =====================
    1. Procedimientos relativos al tratamiento o a la prevención de
    enfermedades.
