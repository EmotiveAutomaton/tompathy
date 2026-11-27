from tompathy_engine.packet.research_labels import label_readings, tag_keys


def test_round37_tag_alias_is_scoped_to_need_readings():
    need = {
        "id": "N3",
        "events": [{"label": "belonging"}],
        "people": {"belonging": 0.5},
        "floor": {},
        "nothing_here": {},
    }
    channel = {"id": "C7", "events": [{"label": "belonging"}]}
    result = label_readings({"on_page": [need, channel]})
    assert result["on_page"][0]["events"] == [{"label": "acceptance"}]
    assert result["on_page"][0]["people"] == {"acceptance": 0.5}
    assert result["on_page"][1]["events"] == [{"label": "belonging"}]
    assert tag_keys({"contact": 1, "acceptance": 2}) == {"contact": 1, "acceptance": 2}
