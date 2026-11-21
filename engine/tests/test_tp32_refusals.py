import numpy as np

from tompathy_engine.eval.readers.tp32 import match_credit, measure, opened, session_totals


def test_only_explicit_dismissals_and_inserted_text():
    ep = {"options":[{"index":0,"original":"a"},{"index":1,"original":"b"}],
          "usable":True,"decision":"edit","verified_insertion":True,
          "selected_index":0,"matched_option_indices":[1]}
    assert opened(ep) == (["a","b"], [], ["b"])
    assert opened(dict(ep, decision="ignore")) == (["a","b"], [], [])
    assert opened(dict(ep, decision="dismiss")) == (["a","b"], ["a","b"], [])
    assert opened(dict(ep, verified_insertion=False)) is None
    assert opened(dict(ep, usable=False)) is None


def test_prompt_centering_multiplicity_and_ties():
    rows = [["s","w","p",3,[[0,0,1],[0],[1]]], ["t","v","q",1,[[1],[1],[]]]]
    sums, counts, _ = session_totals(rows, np.eye(2))
    np.testing.assert_allclose(sums[:,0], 0, atol=1e-12)
    np.testing.assert_allclose(sums[0,1], [1/3,-1/3])
    assert counts[0].tolist() == [3,1,1]
    assert match_credit(np.array([1,1,2]), 1) == .5


def test_different_prompt_only_and_paired_known_answers():
    rows = [[f"{w}-{s}",w,s%2,24,[[0]*20+[1]*20+[2], [w]*20,[2]]]
            for w in range(2) for s in range(4)]
    totals = session_totals(rows, np.eye(3))
    result, archive = measure(rows,*totals,lambda: None)
    assert result["stability"]["passes"]
    assert result["matching"]["baseline"] == .5
    assert result["matching"]["augmented"] == 1
    assert len(archive["queries"]) == 8
    for row in rows:
        row[2] = row[1]
    result, _ = measure(rows,*session_totals(rows,np.eye(3)),lambda: None)
    assert result["matching"] is None
