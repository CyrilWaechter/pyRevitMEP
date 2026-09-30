from viewrename import codec


def test_encode_decode_round_trip_with_accents():
    patterns = {"ViewPlan": "PE_name(ORG_Métier)", "View3D": "name(Sous-catégorie)_3D"}
    assert codec.decode_patterns(codec.encode_patterns(patterns)) == patterns


def test_encode_skips_empty_values_and_sorts_keys():
    assert codec.encode_patterns({"View3D": "B", "ViewPlan": "", "ViewSheet": "A"}) == (
        '{"View3D": "B", "ViewSheet": "A"}'
    )


def test_decode_legacy_single_quoted_dict():
    legacy = "{'ViewPlan': 'PE_name(ORG_Métier)', 'View3D': 'name(X)_3D'}"
    assert codec.decode_patterns(legacy) == {
        "ViewPlan": "PE_name(ORG_Métier)",
        "View3D": "name(X)_3D",
    }


def test_decode_bytes_value():
    assert codec.decode_patterns(b"{'ViewPlan': 'A'}") == {"ViewPlan": "A"}


def test_decode_garbage_returns_empty_dict():
    assert codec.decode_patterns("not a dict") == {}
    assert codec.decode_patterns("") == {}
    assert codec.decode_patterns(None) == {}
    assert codec.decode_patterns([1, 2]) == {}


def test_decode_filters_non_string_and_empty_entries():
    assert codec.decode_patterns('{"ViewPlan": "A", "View3D": "", "ViewSheet": null}') == {"ViewPlan": "A"}


def test_normalize_config_value():
    assert codec.normalize_config_value(b"name(Level)") == "name(Level)"
    assert codec.normalize_config_value(None) == ""
    assert codec.normalize_config_value(42) == "42"
