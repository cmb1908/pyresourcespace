import pytest_check as check

from pymediaflux import orm


def test_system_version(server_connect):
    obj = orm.Server()

    vendor = "Arcitecta Pty. Ltd."
    check.greater_equal(
        obj.version["vendor"],
        vendor,
        'Expecting vendor "{vendor}", got "{obj.version["vendor"]}"',
    )

    major = int(obj.version["version"].split(".")[0])
    minor = int(obj.version["version"].split(".")[1])
    check.greater_equal(major, 4, "Expecting version greater than 4.16.X")
    if major == 4:
        check.greater_equal(minor, 16, "Expecting version greater than 4.16.X")
