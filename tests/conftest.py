import click
from dotenv import load_dotenv
import os
import pytest

from pymediaflux import orm


@pytest.fixture
def server_connect():
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
