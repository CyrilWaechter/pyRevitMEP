from viewrename import pattern


class FakeResolver:
    def __init__(self, values):
        self.values = values

    def by_name(self, name):
        return self.values.get("name:" + name, "")

    def by_bip(self, name):
        return self.values.get("bip:" + name, "")

    def by_guid(self, guid):
        return self.values.get("guid:" + guid, "")


def test_substitutes_name_bip_and_guid():
    resolver = FakeResolver(
        {
            "name:ORG_Métier": "CVC",
            "bip:PLAN_VIEW_LEVEL": "L1",
            "guid:62444aa5-69f7-4aa6-9b0e-238dd1309f83": "Partagé",
        }
    )
    result = pattern.apply_pattern(
        "name(ORG_Métier)_bip(PLAN_VIEW_LEVEL)_Guid('62444aa5-69f7-4aa6-9b0e-238dd1309f83')",
        resolver,
    )
    assert result == "CVC_L1_Partagé"


def test_unknown_references_resolve_to_empty_string():
    resolver = FakeResolver({})
    assert pattern.apply_pattern("pre_name(Missing)_post", resolver) == "pre__post"


def test_plain_text_passes_through_with_parentheses():
    resolver = FakeResolver({})
    assert pattern.apply_pattern("Plan (niveau)name(Level)", resolver) == "Plan (niveau)"


def test_validate_accepts_valid_pattern():
    assert pattern.validate_pattern("name(ORG_Métier)_bip(PLAN_VIEW_LEVEL)") == []


def test_validate_rejects_unbalanced_parentheses():
    assert pattern.validate_pattern("name(Level") != []


def test_validate_rejects_unknown_reference():
    assert pattern.validate_pattern("foo(bar)") != []


def test_validate_ignores_parentheses_without_leading_word():
    assert pattern.validate_pattern("Plan (sans reference)") == []


def test_validate_accepts_text_glued_to_reference():
    assert pattern.validate_pattern("PEnname(Level)") == []


def test_validate_rejects_short_guid():
    assert pattern.validate_pattern("Guid('AAAA')") != []


def test_validate_rejects_empty_reference_arguments():
    assert pattern.validate_pattern("name()") != []
    assert pattern.validate_pattern("bip( )") != []


def test_guid_reference_accepts_dashless_guid():
    dashless = "62444aa569f74aa69b0e238dd1309f83"
    resolver = FakeResolver({"guid:" + dashless: "Partagé"})
    assert pattern.apply_pattern(f"Guid('{dashless}')", resolver) == "Partagé"
    assert pattern.validate_pattern(f"Guid('{dashless}')") == []


def test_reference_matches_returns_positions():
    assert pattern.reference_matches("PE_name(Level)_3D") == [(3, 14, "name", "name(Level)")]


def test_reference_matches_plain_text_is_empty():
    assert pattern.reference_matches("Plan (niveau)") == []
