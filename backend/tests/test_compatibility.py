from app.services.compatibility import (
    bounds_overlap,
    check_resolution,
)


def test_bounds_overlap():

    bounds_a = [0, 0, 10, 10]
    bounds_b = [5, 5, 15, 15]

    assert bounds_overlap(
        bounds_a,
        bounds_b
    ) is True


def test_bounds_do_not_overlap():

    bounds_a = [0, 0, 10, 10]
    bounds_b = [20, 20, 30, 30]

    assert bounds_overlap(
        bounds_a,
        bounds_b
    ) is False


def test_resolution_within_tolerance():

    class FakeRow:

        def __init__(self, x, y):
            self.data = {
                "resolution_x": x,
                "resolution_y": y
            }

        def __getitem__(self, key):
            return self.data[key]

    rows = [
        FakeRow(10, 10),
        FakeRow(10.5, 10.5)
    ]

    assert check_resolution(rows) is True


def test_resolution_outside_tolerance():

    class FakeRow:

        def __init__(self, x, y):
            self.data = {
                "resolution_x": x,
                "resolution_y": y
            }

        def __getitem__(self, key):
            return self.data[key]

    rows = [
        FakeRow(10, 10),
        FakeRow(15, 15)
    ]

    assert check_resolution(rows) is False