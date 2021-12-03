"""
https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html
"""
import functools
import os
from typing import NamedTuple, Optional, List

from umlsrat.util.shitty_df import ShittyDF

_THIS_DIR = os.path.dirname(os.path.normpath(__file__))
_VOCABULARIES_CSV = os.path.join(_THIS_DIR, 'vocabularies.csv')


@functools.lru_cache(maxsize=1)
def VOCAB_INFO() -> ShittyDF:
    return ShittyDF(_VOCABULARIES_CSV, 'Abbreviation')


def normalize_abbrev(abbrev: str) -> str:
    norm = abbrev.strip().upper()
    return _MM_CODE_SYS_MAP.get(norm, norm)


def get_vocab_info(abbrev: str) -> Optional[NamedTuple]:
    norm = normalize_abbrev(abbrev)
    voc_info = VOCAB_INFO()
    return voc_info.get(norm)


def validate_vocab_abbrev(abbrev: str) -> str:
    info = get_vocab_info(abbrev)
    if not info:
        message = "Unknown vocabulary abbreviation: '{}'. Try one of these: {}".format(
            abbrev, "\n".join(str(_) for _ in VOCAB_INFO().values())
        )
        raise ValueError(message)
    return info.Abbreviation


@functools.lru_cache(maxsize=2)
def vocabs_for_language(lang: str) -> List[str]:
    return [info.Abbreviation
            for info in VOCAB_INFO().values()
            if info.Language == lang]


_MM_CODE_SYS_MAP = {
    'SNOMED-CT': 'SNOMEDCT_US',
    'SNOMED': 'SNOMEDCT_US'
}

"""
  RXNORM("RxNorm", "2.16.840.1.113883.6.88", "rxnorm", "RXNORM", new int[]{1552, 36989}),
  LOINC("LOINC", "2.16.840.1.113883.6.1", "loinc", (String)null, new int[]{5102, 32992}),
  CPT("CPT-4", "2.16.840.1.113883.6.12", "cpt", "CPT", new int[]{20}),
  ICD9_CM("ICD-9-CM", "2.16.840.1.113883.6.2", "icd9", "ICD9", new int[]{10}),
  ICD9_DIAGNOSIS("ICD-9-CM Diagnosis", "2.16.840.1.113883.6.103", "icd9diagnosis", "ICD-9 Diagnoses", new int[0]),
  ICD9_PROCEDURE("ICD-9-CM Procedure", "2.16.840.1.113883.6.104", "icd9procedure", "ICD-9 Procedures", new int[0]),
  ICD10_CM("ICD-10-CM", "2.16.840.1.113883.6.90", "icd10cm", "ICD-10 CM", new int[]{5140}),
  ICD10_PCS("ICD-10-PCS", "2.16.840.1.113883.6.4", "icd10pcs", (String)null, new int[]{5150}),
  HCPCS("HCPCS", "2.16.840.1.113883.6.14", "hcpcs", (String)null, new int[0]),
  HCPCS_II("HCPCS-LEVEL-II", "2.16.840.1.113883.6.285", "hcpcs2", (String)null, new int[]{1015}),
  CVX("CVX", "2.16.840.1.113883.12.292", "cvx", (String)null, new int[]{33060}),
  ATC("ATC", "2.16.840.1.113883.6.77", "atc", (String)null, new int[]{5340}),
  RADLEX("RadLex", "2.16.840.1.113883.6.256", "radlex", (String)null, new int[0]),
  SNOMED("SNOMED-CT", "2.16.840.1.113883.6.96", "snomed", "SNOMED", new int[]{36, 54981}),
  MSDRG("MS-DRG", "2.16.840.1.113883.12.55", "msdrg", (String)null, new int[]{5280}),
  PATIENTCLASS("PatientClass", "2.16.840.1.113883.12.4", "patientclass", (String)null, new int[0]),
  ICD10_GM("ICD-10-GM", "2.16.840.1.113883.3.232.99.155", "icd10gm", "ICD-10 GM", Locale.GERMAN, new int[0]),
  OPS("OPS", "2.16.840.1.113883.3.232.99.157", "ops", "OPS", Locale.GERMAN, new int[0]),
  ATC_GM("ATC-GM", "2.16.840.1.113883.3.21.42.510", "atcgm", "ATC GM", Locale.GERMAN, new int[0]),
  UCUM("Unified Code for Units of Measure", "2.16.840.1.113883.6.8", "ucum", "UCUM", new int[0]),
  FDAROA("FDA Route of Administration", "2.16.840.1.113883.3.26.1.1", "fdaroa", (String)null, new int[0]),
  ADMINISTRATIVEGENDER("AdministrativeGender", "2.16.840.1.113883.5.1", "administrativeGender", (String)null, new int[]{37000}),
  MMODAL_ACUITY("MModal-Acuity", "2.16.840.1.113883.3.21.42.Acuity", "mmodalAcuity", (String)null, new int[]{37001}),
  MMODAL_CERTAINTY("MModal-Certainty", "2.16.840.1.113883.3.21.42.Certainty", "mmodalCertainty", (String)null, new int[]{37002}),
  MMODAL_DIAGNOSISTYPE("MModal-DiagnosisType", "2.16.840.1.113883.3.21.42.DiagnosisType", "mmodalDiagnosisType", (String)null, new int[]{37003}),
  MMODAL_LATERALITY("MModal-Laterality", "2.16.840.1.113883.3.21.42.Laterality", "mmodalLaterality", (String)null, new int[]{37004}),
  MMODAL_SUBJECT("MModal-Subject", "2.16.840.1.113883.3.21.42.Subject", "mmodalSubject", (String)null, new int[]{37005}),
  MMODAL_TEMPORALITY("MModal-Temporality", "2.16.840.1.113883.3.21.42.Temporality", "mmodalTemporality", (String)null, new int[]{37006}),
  MMODAL_ALERT("MModal-Alert", "2.16.840.1.113883.3.21.42.407", "mmodalAlert", (String)null, new int[]{37007}),
  MMODAL_PLANFOR("MModal-PlanFor", "2.16.840.1.113883.3.21.42.408", "mmodalPlanFor", (String)null, new int[]{37008}),
  MMODAL_STATUS("MModal-Status", "2.16.840.1.113883.3.21.42.Status", "mmodalStatus", (String)null, new int[]{37009}),
  MMODAL_CARDINALITY("MModal-Cardinality", "2.16.840.1.113883.3.21.42.Cardinality", "mmodalCardinality", (String)null, new int[]{37010}),
  MMODAL_PLANS("MModal-Plans", "2.16.840.1.113883.3.21.42.Plans", "mmodalPlans", (String)null, new int[]{37011}),
  MMODAL_PLANSTATE("MModal-PlanState", "2.16.840.1.113883.3.21.42.PlanState", "mmodalPlanState", (String)null, new int[]{37012}),
  MMODAL_CONSTRAINT("MModal-Constraint", "2.16.840.1.113883.3.21.42.Constraint", "mmodalConstraint", (String)null, new int[]{37013}),
  MMODAL_CUSTOMER("MModal-Customer", "2.16.840.1.113883.3.21.42.Customer", "mmodalCustomer", (String)null, new int[]{37014}),
  MMODAL_VISITTYPE("MModal-VisitType", "2.16.840.1.113883.3.21.42.VisitType", "mmodalVisitType", (String)null, new int[]{37015}),
  MMODAL_PATIENTAGE("MModal-PatientAge", "2.16.840.1.113883.3.21.42.PatientAge", "mmodalPatientAge", (String)null, new int[]{37016}),
  MMODAL_CAC("MModal-CAC", "2.16.840.1.113883.3.21.42.CAC", "mmodalCAC", (String)null, new int[]{37017}),
  MMODAL_EM("MModal-EM", "2.16.840.1.113883.3.21.42.EM", "mmodalEM", (String)null, new int[]{37022}),
  MMODAL_WORDLIST("MModal-WordList", "2.16.840.1.113883.3.21.42.WordList", "mmodalCSList", (String)null, new int[]{37018}),
  OBSERVATION("ObservationInterpretation", "2.16.840.1.113883.5.83", "observation", "Observation", new int[]{37019}),
  MMODAL_DOCUMENTTYPE("MModal-DocumentType", "2.16.840.1.113883.3.21.42.DocumentType", "mmodalDocumentType", (String)null, new int[]{37020}),
  MMODAL_ENCOUNTERTYPE("MModal-EncounterType", "2.16.840.1.113883.3.21.42.EncounterType", "mmodalEncounterType", (String)null, new int[]{37021}),
  MMODAL_USECASE("MModal-UseCase", "2.16.840.1.113883.3.21.42.UseCase", "mmodalUseCase", (String)null, new int[0]),
  MMODAL_RULETYPE("MModal-RuleType", "2.16.840.1.113883.3.21.42.RuleType", "mmodalRuleType", (String)null, new int[0]),
  MMODAL_REPORTER("MModal-Reporter", "2.16.840.1.113883.3.21.42.Reporter", "mmodalReporter", (String)null, new int[0]),
  MMODAL_VALUE_SETS("MModal-ValueSets", "2.16.840.1.113883.3.21.42.ValueSets", "mmodalValueSets", "ValueSets", new int[]{36233}),
  MMODAL_RULES("MModal-Rules", "2.16.840.1.113883.3.21.42.Rules", "mmodalRules", (String)null, new int[0]),
  HCC("HCC", "2.16.840.1.113883.3.21.42.410", "hcc", (String)null, new int[0]),
  HCC_PACE("HCC-PACE", "2.16.840.1.113883.3.21.42.411", "hccPace", (String)null, new int[0]),
  RX_HCC("Rx-HCC", "2.16.840.1.113883.3.21.42.412", "rxHcc", (String)null, new int[0]),
  HCC_COMMERCIAL("HCC-COMMERCIAL", "2.16.840.1.113883.3.21.42.413", "hccCommercial", (String)null, new int[0]),
  MMODAL_MIMS("MModal-Mims", "2.16.840.1.113883.3.21.42.Mims", "mmodalMims", (String)null, new int[0]),
  MMODAL_ASSISTANT("MModal-Assistant", "2.16.840.1.113883.3.21.42.Assistant", "mmodalAssistant", (String)null, new int[]{37023}),
  MMODAL_EXTVOCAB("MModal-ExternalVocabulary", "2.16.840.1.113883.3.21.42.ExtVocab", "mmodalExtVocab", (String)null, new int[0]),
  MMODAL("MMODAL", "2.16.840.1.113883.3.21.1", "mmodal", (String)null, new int[0]),
  MM_LOINC("MM-LOINC", "2.16.840.1.113883.3.21", "mmLoinc", "MModal Sections", new int[0]),
  MM_RAD_LOINC("MM-RAD-LOINC", "2.16.840.1.113883.3.21.42.501", "mmRadLoinc", "MModal Radiology Sections", new int[0]),
  MM_PATH_LOINC("MM-PATH-LOINC", "2.16.840.1.113883.3.21.42.502", "mmPathLoinc", "MModal Pathology Sections", new int[0]),
  MMODAL_WSD("MMODAL-WSD", "2.16.840.1.113883.3.21.42.WSD", "mmodalWSD", "MModal Word Sense Disambiguation", new int[0]);
"""
