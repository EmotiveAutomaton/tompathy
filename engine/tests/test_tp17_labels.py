import pytest

from tompathy_engine.eval.readers.tp17 import supplied_label


@pytest.mark.parametrize('raw', ['__caring__', 'caring'])
def test_publisher_label_matches_original_source(raw):
    assert supplied_label(raw, ['caring', 'sad'], 'caring') == 'caring'


@pytest.mark.parametrize('raw,source', [
    ('__sad__', 'caring'), ('__unknown__', 'unknown'),
    ('_caring_', 'caring'), ('__caring', 'caring'),
    ('__CARING__', 'caring'), ('____caring____', 'caring'),
])
def test_label_mismatch_is_not_silently_remapped(raw, source):
    with pytest.raises(ValueError, match='original ED label'):
        supplied_label(raw, ['caring', 'sad'], source)
