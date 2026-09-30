from viewrename import apply


class FakeDuplicate(Exception):
    pass


class FakeResolver:
    def __init__(self, values):
        self.values = values

    def by_name(self, name):
        return self.values.get(name, "")

    def by_bip(self, name):
        return ""

    def by_guid(self, guid):
        return ""


class FakeView:
    taken = None  # set of already-used names when conflict simulation is on

    def __init__(self, name, class_name):
        self._name = name
        self._class_name = class_name

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        if FakeView.taken is not None:
            if value in FakeView.taken:
                raise FakeDuplicate(value)
            FakeView.taken.add(value)
        self._name = value


def make_view(name, class_name):
    return type(class_name, (FakeView,), {})(name, class_name)


def test_compute_renames_uses_pattern_per_class():
    view = make_view("old", "ViewPlan")
    renames = apply.compute_renames(
        [view], {"ViewPlan": "P_name(Level)"}, resolver_factory=lambda v: FakeResolver({"Level": "L1"})
    )
    assert renames == [(view, "P_L1")]


def test_compute_renames_skips_unconfigured_class():
    view = make_view("old", "View3D")
    assert apply.compute_renames([view], {"ViewPlan": "P"}, resolver_factory=FakeResolver) == []


def test_rename_views_disambiguates_duplicates():
    FakeView.taken = set()
    try:
        first = make_view("a", "ViewPlan")
        second = make_view("b", "ViewPlan")
        renamed, failed = apply.rename_views([(first, "X"), (second, "X")], duplicate_exception=FakeDuplicate)
        assert renamed == [("a", "X"), ("b", "X 1")]
        assert failed == []
    finally:
        FakeView.taken = None


def test_rename_views_suffixes_around_names_outside_the_batch():
    FakeView.taken = {"X"}
    try:
        first = make_view("a", "ViewPlan")
        second = make_view("b", "ViewPlan")
        renamed, failed = apply.rename_views([(first, "X"), (second, "X")], duplicate_exception=FakeDuplicate)
        assert renamed == [("a", "X 1"), ("b", "X 2")]
        assert failed == []
    finally:
        FakeView.taken = None


def test_rename_views_reports_failures_and_continues():
    class AlwaysFails:
        @property
        def Name(self):
            return "a"

        @Name.setter
        def Name(self, value):
            raise FakeDuplicate(value)

    renamed, failed = apply.rename_views([(AlwaysFails(), "X")], duplicate_exception=FakeDuplicate)
    assert renamed == []
    assert failed and failed[0][0] == "a"


def test_preview_lines_truncates():
    views = [make_view(str(i), "ViewPlan") for i in range(15)]
    lines = apply.preview_lines([(v, "n" + v.Name) for v in views], limit=3)
    assert lines == ["0 -> n0", "1 -> n1", "2 -> n2", "... and 12 more"]


def test_format_report_lists_sections():
    report = {
        "scope": "selected views",
        "cancelled": False,
        "renamed": [("old", "new")],
        "failed": [("bad", "boom")],
        "skipped": {"no_pattern": ["X"], "template": [], "not_view": []},
    }
    text = apply.format_report(report)
    assert "renamed 1" in text
    assert "old -> new" in text
    assert "bad -> boom" in text
    assert "X" in text
