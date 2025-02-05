import pytest_check as check

from pymediaflux import orm


def test_dam_731_base_10_checksum(server_connect):
    dam2 = orm.Asset.query_name("DAM-2")

    for asset in dam2.assets_all:
        if asset.is_collection:
            continue
        check.not_equal(
            asset.checksum(10), "", f"Expecting a base 10 checksum on {asset.name}"
        )


def test_dam_731_base_16_checksum(server_connect):
    dam2 = orm.Asset.query_name("DAM-2")

    for asset in dam2.assets_all:
        if asset.is_collection:
            continue
        check.not_equal(
            asset.checksum(16), "", f"Expecting a base 16 checksum on {asset.name}"
        )
