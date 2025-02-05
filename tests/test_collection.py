import pytest_check as check

from pymediaflux import orm


def test_collection_count(server_connect):
    obj = orm.Collection("7069835")

    check.greater_equal(obj.count, 6, f"Expecting 6 DAM-2 assets, got {obj.count}")
    check.greater_equal(
        obj.count_all,
        127,
        f"Expecting 127 DAM-2 assets (including nesting), got {obj.count_all}",
    )


def test_collection_members(server_connect):
    obj = orm.Collection("7069835")

    check.greater_equal(
        obj.count,
        len(list(obj.members)),
        f"Expecting count({obj.count}) to match member length {len(list(obj.members))}",
    )
