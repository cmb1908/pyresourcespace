import pytest_check as check

from pymediaflux import orm


def test_collection_count(server_connect):
    obj = orm.Collection("7069835")

    check.greater_equal(obj.count, 149, f"Expecting 149 DAM-2 assets, got {obj.count}")


def test_collection_members(server_connect):
    obj = orm.Collection("7069835")

    check.greater_equal(
        obj.count,
        len(list(obj.members)),
        f"Expecting count({obj.count}) to match member length {len(list(obj.members))}",
    )
