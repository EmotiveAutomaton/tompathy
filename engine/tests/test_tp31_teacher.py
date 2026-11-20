import pytest

from tompathy_engine.eval.readers.tp31_teacher import (
    SOURCES,
    agreement_panel,
    binary_kappa,
    known_group,
    sentence_rows,
    teacher_checks,
    text_pin,
    valid_label,
)


def label(change):
    return {'change': change, 'whose': 'writer' if change else 'nobody',
            'when': 'already' if change else 'none'}


def test_schema_rejects_coercion_extra_keys_and_inconsistent_answers():
    assert valid_label(label(True)) == label(True)
    assert valid_label(label(False)) == label(False)
    for value in [dict(label(True), change=1), dict(label(False), when='ahead'),
                  dict(label(True), whose='nobody'), dict(label(True), extra=0), None]:
        assert valid_label(value) is None


def test_acceptance_exclusion_precedes_sentence_selection_and_rejects_duplicate_ids():
    docs = [{'source': 'ed', 'group': 'conversation', 'id': 'x', 'text': 'Protected text. Other text.'},
            {'source': 'story', 'group': 'story', 'id': 'y', 'text': 'PROTECTED   TEXT.'}]
    rows, omitted = sentence_rows(docs, {text_pin('Protected text.')})
    assert omitted == 2 and len(rows) == 1 and rows[0]['text'] == 'Other text.'
    rows, omitted = sentence_rows(docs[:1], {text_pin(docs[0]['text'])})
    assert rows == [] and omitted == 2
    with pytest.raises(ValueError, match='Duplicate'):
        sentence_rows(docs+docs, set())


def test_panel_is_fixed_source_balanced_and_independent_of_row_order():
    rows = [{'id': f'{source}-{i}', 'source': source} for source in SOURCES for i in range(340)]
    selected = agreement_panel(rows)
    assert len(selected) == 2000 and selected == agreement_panel(list(reversed(rows)))
    assert [sum(r['source'] == s for r in selected) for s in SOURCES] == [334,334,333,333,333,333]
    with pytest.raises(ValueError, match='six registered'):
        agreement_panel([r for r in rows if r['source'] != 'go'])


def test_kappa_known_cases_and_invalid_coverage():
    first = [label(i < 50) for i in range(100)]
    second = [label(i < 40 or 50 <= i < 60) for i in range(100)]
    assert binary_kappa(first, second)['kappa'] == pytest.approx(.6)
    assert binary_kappa(first, first)['kappa'] == 1
    assert binary_kappa([label(True)]*100, [label(True)]*100)['kappa'] is None
    result = binary_kappa(first, [None]+first[1:])
    assert result['validPairs'] == 99 and result['kappa'] == 1


def test_unknown_known_group_labels_cannot_improve_a_gate():
    row = known_group([label(True)]*84+[label(False)]*15+[None], minimum=.85)
    assert row['rate'] > .84 and row['lowerRate'] == .84 and not row['passes']
    row = known_group([label(True)]*20+[label(False)]*79+[None], maximum=.2)
    assert row['upperRate'] == .21 and not row['passes']


def test_all_teacher_checks_required_before_student():
    panel = [label(i%2 == 0) for i in range(2000)]
    groups = {'envent-feeling': [label(True)]*85+[label(False)]*15,
              'ed': [label(True)]*90+[label(False)]*10,
              'stack': [label(True)]*20+[label(False)]*80}
    assert teacher_checks(panel, panel, groups)['qualifiesForStudent']
    failed = teacher_checks(panel, [None]+panel[1:], groups)
    assert not failed['qualifiesForStudent'] and failed['agreement']['validPairs'] == 1999
    with pytest.raises(ValueError):
        teacher_checks(panel[:1999], panel[:1999], groups)
