import pytest_check as check

from pymediaflux import orm


def test_filter_namespace_count(server_connect):
    spaces = orm.Namespace.filter_spaces()

    # Should have more than 5
    check.greater_equal(
        len(spaces), 5, f"Expecting at least 5 spaces, got {len(spaces)}"
    )


def test_filter_namespace_powerhouse_toi(server_connect):
    spaces = orm.Namespace.filter_spaces()

    # powerhouse-toi should be in there
    check.is_in("powerhouse-toi", [x.namespace for x in spaces])


def test_filter_namespace_label(server_connect):
    toi_ns = orm.Namespace("powerhouse-toi")

    # powerhouse-toi label should be...
    check.equal("02. Thing of Interest", toi_ns.label)


def test_filter_namespace_list(server_connect):
    toi_ns = orm.Namespace("powerhouse-toi")

    check.equal(2, len(toi_ns.filters))
