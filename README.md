UMLS RAT
=========

UMLS RAT (**R**EST **A**PI **T**ool) provides a reasonable interface to
the [UMLS Metathesaurus](https://uts.nlm.nih.gov/uts/umls/home) via
the [REST API](https://documentation.uts.nlm.nih.gov/rest/home.html).

Definitions
===========

At this time, this repository is mostly used to find definitions for concepts in SNOMED, etc where
definitions are not provided. The script `definitions-dump.py` provides example usage. 

Get definitions for this out-dated "back" concept: `450807008`

```bash
python definitions-dump.py --source-code=450807008 --source-vocab=SNOMEDCT_US --api-key=${UMLS_API_KEY}
```
    ...
    Back structure, including back of neck
    ======================================
    1. subdivision of body proper, each instance of which has as its
    direct parts some back of neck and some back of trunk. Examples: There
    is only one back of body proper.


Now get one in Spanish

```bash
python definitions-dump.py --source-code=450807008 --source-vocab=SNOMEDCT_US --target-language=SPA --api-key=${UMLS_API_KEY}
```
    ...
    Body Regions
    ============
    1. Áreas anatómicas del cuerpo.


Look for a concept using the description only

```bash
python definitions-dump.py --source-desc="Physical therapy" --target-language=SPA --api-key=${UMLS_API_KEY}
```
    ...
    Rehabilitation therapy
    ======================
    1. Recuperación de las funciones humanas, al mayor grado posible, en
    una perosna o personas que padecen enfermedad o lesión.

    Therapeutic procedure
    =====================
    1. Procedimientos relativos al tratamiento o a la prevención de
    enfermedades.
