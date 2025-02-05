import pytest_check as check

from pymediaflux import orm


def test_dam_23(server_connect):
    dam2 = orm.Asset.query_name("DAM-2")

    # Need to build a list of expected paths
    # Only works one level deep
    path = {dam2.id: "/"}
    for asset in dam2.assets:
        path[asset.id] = f"/{asset.name}/"
    for asset in dam2.assets_all:
        if asset.is_collection:
            continue
        check.equal(
            asset.mf_source_name,
            path[asset.parent] + asset.mf_name,
            f"Check of source path failed for {asset.mf_source_name} ({asset.id})",
        )
