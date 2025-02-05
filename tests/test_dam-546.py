import pytest_check as check

from pymediaflux import orm


def test_dam_546_success(server_connect):
    version = orm.Server().version

    check.is_not_none(version, "Server connection failed")


def test_dam_729_fail(server_connect):
    orm.Request.headers = {
        "Content-Type": "application/xml",
        "mediaflux.api.token.app": "api",
    }

    try:
        version = orm.Server().version
        check.is_true(False, "Authentication succeeded with no authentication")
    except ValueError:
        check.is_true(True)
        pass
