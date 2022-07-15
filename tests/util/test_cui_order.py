from umlsrat.util import cui_order


def test_sem_type_name_sim(api, rng):
    topic_results_n = 50
    # this test is pretty contrived, but....
    surgery = [
        _.get("ui") for _ in api.search(query="surgery", max_results=topic_results_n)
    ]
    automobile = [
        _.get("ui") for _ in api.search(query="automobile", max_results=topic_results_n)
    ]

    sset = set(surgery)
    aset = set(automobile)

    # non overlapping
    assert not sset & aset

    def num_surgery(other):
        return len(set(other) & sset)

    def num_auto(other):
        return len(set(other) & aset)

    # create ordering based on first cui
    surgery_sim = cui_order.sem_type_name_sim(api, source_cui=surgery[0])
    automobile_sim = cui_order.sem_type_name_sim(api, source_cui=automobile[0])

    # mix together the rest
    mixed = surgery[1:] + automobile[1:]
    rng.shuffle(mixed)

    surgery_sorted = sorted(mixed, key=surgery_sim)
    auto_sorted = sorted(mixed, key=automobile_sim)

    # First half of surgery sorted should have more surgery than auto
    assert num_surgery(surgery_sorted[:topic_results_n]) > num_auto(
        surgery_sorted[:topic_results_n]
    )
    assert num_surgery(surgery_sorted[:topic_results_n]) / topic_results_n > 0.8
    # vice versa for auto
    assert num_surgery(auto_sorted[:topic_results_n]) < num_auto(
        auto_sorted[:topic_results_n]
    )
    assert num_auto(auto_sorted[:topic_results_n]) / topic_results_n > 0.8
