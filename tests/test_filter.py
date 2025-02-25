import pytest
import pytest_check as check

from pymediaflux import orm


def test_filter_description(server_connect):
    f = orm.Filter("powerhouse-toi", "Name")

    check.equal("Thing of Interest Name", f.description)


def test_filter_label(server_connect):
    f = orm.Filter("powerhouse-toi", "irn")

    check.equal("TOI IRN", f.label)


def test_filter_toi_irn(server_connect):
    results = orm.Asset.query("filter 'powerhouse-toi:irn(value=\\'234\\')'")

    check.greater_equal(
        len(results), 5, f"Expecting at least 5 results, got {len(results)}"
    )


def test_filter_toi_irn_in_toi(server_connect):
    results = orm.Asset.query(
        "filter 'powerhouse-toi:irn(value=\\'234\\')' and asset has parent collection 5642820"
    )

    check.equal(len(results), 3, f"Expecting 3 results, got {len(results)}")


@pytest.mark.timeout(5)
def test_filter_query(query_str):

    orm.Asset.query(query_str)
