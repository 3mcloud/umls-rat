from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import definitions
from umlsrat.lookup.umls import find_umls

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = MetaThesaurus(rklopfer_api_key)


def find_single_mesh_def(snomed_code: str) -> str:
    cui = find_umls(api, "SNOMEDCT_US", snomed_code)
    def_dict = definitions.definitions_bfs(api, cui, min_num_defs=1, target_vocabs=('MSH',)).pop()
    return def_dict['value']


def test_old_back():
    # old back
    definition = find_single_mesh_def('450807008')
    assert definition == 'The rear surface of an upright primate from the shoulders to the hip, ' \
                         'or the dorsal surface of tetrapods.'


def test_wrist():
    # Closed fracture of left wrist (10937761000119101)
    definition = find_single_mesh_def('10937761000119101')
    assert definition == 'Injuries to the wrist or the wrist joint.'


def test_find_definitions():
    data = definitions.find_definitions(api, 'snomed', '282024004', min_num_defs=2, target_lang='ENG')
    values = [_['value'] for _ in data]
    assert values == ['region of the back between thorax and pelvis.',
                      'The part of the spine in the lower back that consists of the lumbar region and the sacrum.',
                      'Region of the back including the LUMBAR VERTEBRAE, SACRUM, and nearby structures.']


def test_find_room_air():
    data = definitions.find_definitions(api, source_vocab='snomed',
                                        source_code='37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2',
                                        source_desc='Room air (substance)',
                                        min_num_defs=2)
    values = [_['value'] for _ in data]
    assert values == ['Unmodified air as existing in the immediate surroundings.',
                      "The mixture of gases present in the earth's atmosphere consisting of oxygen, nitrogen, carbon dioxide, and small amounts of other gases.",
                      "A mixture of gases making up the earth's atmosphere, consisting mainly of nitrogen, oxygen, argon, and carbon dioxide."]


def test_find_low_suspicion():
    data = definitions.find_definitions(api, source_vocab='snomed',
                                        source_code='c917af35-7249-4ec6-9062-68e6b83ff82a',
                                        source_desc="Low suspicion",
                                        min_num_defs=2)
    values = [_['value'] for _ in data]
    assert values


def test_find_poa():
    # INFO:definitions.py:Finding definitions of snomed/ []
    data = definitions.find_definitions(api, source_vocab='snomed',
                                        source_code='6c8c4505-926c-4ebb-805d-5c73fb650e3c',
                                        source_desc="Present on admission (qualifier value)",
                                        min_num_defs=2)
    values = [_['value'] for _ in data]
    assert values


def test_find_without_code():
    data = definitions.find_definitions(api, source_desc="Cancer")
    values = [_['value'] for _ in data]
    assert values


def test_find_spanish():
    data = definitions.find_definitions(api, source_desc="Cancer", target_lang='SPA')
    values = [_['value'] for _ in data]
    assert values
