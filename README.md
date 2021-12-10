UMLS RAT
=========

UMLS **R**EST **A**PI **T**ool (RAT) provides a reasonable interface to
the [UMLS Metathesaurus](https://uts.nlm.nih.gov/uts/umls/home) via
the [REST API](https://documentation.uts.nlm.nih.gov/rest/home.html).

Definitions
===========

At this time, this repository is mostly used to find definitions for concepts in SNOMED, etc where
definitions are not provided. The script `definitions-dump.py` provides example usage. 

Get definitions for this out-dated "back" concept: `450807008`

```bash
python definitions-dump.py --source-code=450807008 --source-vocab=SNOMEDCT_US --num-defs=2
```
    ...
    Back structure, including back of neck
    ======================================
    (1) subdivision of body proper, each instance of which has as its
    direct parts some back of neck and some back of trunk. Examples: There
    is only one back of body proper.
    
    Back
    ====
    (1) posterior part of the trunk from the neck to the pelvis.
    (2) The rear surface of an upright primate from the shoulders to the
    hip, or the dorsal surface of tetrapods.
    (3) subdivision of trunk, each instance of which has as its
    constitutional part some complete set of vertebral arches (T1-S5) and
    anatomical entities located posterior to them: together with front of
    trunk constitutes the trunk. Examples: There is only one back.
    (4) The back or upper side of an animal.

Now get one in Spanish

```bash
python definitions-dump.py --source-code=450807008 --source-vocab=SNOMEDCT_US --num-defs=1 --target-language=SPA
```
    ...
    Back
    ====
    (1) La superficie posterior de un primate en posición vertical desde
    los hombros hasta la cadera, o la superficie dorsal de los tetrápodos.


Look for a concept using the description only

```bash
python definitions-dump.py --source-desc="Physical therapy" --num-defs=1 --target-language=SPA
```
    ...
    Health Occupations
    ==================
    (1) Profesiones u otras actividades de negocios dirigidas a la cura y
    prevención de enfermedades. Para las ocupaciones de personal médico
    que no es médico pero que trabaja en los campos de la tecnología
    médica, terapia física, etc. puede consultar OCUPACIONES ASOCIADAS A
    LA SALUD.
