import pytest_check as check

from pymediaflux import orm


def test_dam_729_mime(server_connect):
    dam2 = orm.Asset.query_name("DAM-2")

    mime = {
        "jpg": "image/jpeg",
        "tif": "image/tiff",
        "dng": "image/x-adobe-dng",
        "pdf": "application/pdf",
        "mp4": "video/mp4",
    }
    for asset in dam2.assets:
        check.equal(
            asset.mimetype,
            mime[asset.extension],
            f'Asset({asset.id}, {asset.name}) Bad mime-type "{asset.mimetype}", expected "{mime[asset.extension]}"',
        )


def test_dam_729_exif(server_connect):
    dam2 = orm.Asset.query_name("DAM-2")

    for asset in dam2.assets:
        if asset.mimetype[:5] == "image" and not asset.name == "m83.tif":
            # m83.tif had no exif data
            check.is_true(
                asset.has_exif, f"Asset({asset.id}, {asset.name}) has no exif"
            )
