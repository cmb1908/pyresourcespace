import click
from dotenv import load_dotenv
import itertools
from lxml import etree
import os
import pytest

from pymediaflux import orm


def _server_connect():
    # Load environment variables from .env file
    load_dotenv()

    API_HOST = os.getenv("API_HOST")
    API_PORT = os.getenv("API_PORT")
    API_TOKEN = os.getenv("API_TOKEN")

    # Validate required parameters
    if not API_HOST or not API_TOKEN:
        click.echo("Error: API_HOST and API_TOKEN are required.", err=True)
        return

    # Construct the base URL
    if API_PORT:
        url = f"http://{API_HOST}:{API_PORT}/__mflux_svc__"
    else:
        url = f"http://{API_HOST}/__mflux_svc__"

    # Set headers
    headers = {
        "Content-Type": "application/xml",
        "mediaflux.api.token": f"{API_TOKEN}",
        "mediaflux.api.token.app": "api",
    }

    orm.Request.url = url
    orm.Request.headers = headers


@pytest.fixture
def server_connect():
    _server_connect()


def pytest_generate_tests(metafunc):
    # Tests for known query strings.  We generate srtineg for every operation in every filter
    if "query_str" in metafunc.fixturenames:
        params = []
        _server_connect()
        namespaces = orm.Namespace().filter_spaces()

        for ns in namespaces:
            for f in ns.filters:
                ops = {
                    arg.name: {
                        "asset-id": [100],
                        "date": ["01-Jan-2024"],
                        "integer": [100],
                        "string": ["hello"],
                        "enumeration": arg.restrictions.values(),
                    }[arg.type]
                    for arg in f.args
                }
                for c in itertools.product(*ops.values()):
                    # Zip the dictionary keys with the current combination to form a new dictionary
                    args = dict(zip(ops.keys(), c))
                    params.append(f.query_str(**args))

        metafunc.parametrize("query_str", params)
