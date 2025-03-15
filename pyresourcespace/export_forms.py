import click
from dotenv import load_dotenv
from lxml import etree
import os

from . import orm


def dump(directory: str):
    forms = orm.Form.forms()

    for form in forms:
        form.export(f"{directory}/{form.name}.xml")


@click.command()
@click.option("--api-host", required=False, help="API host (e.g., api.example.com)")
@click.option("--api-port", required=False, help="API port (optional)")
@click.option("--api-token", required=False, help="API token for authentication")
@click.argument("directory")
def main(api_host, api_port, api_token, directory):
    """
    Sends a request to the MediaFlux API to fetch server version details.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve values from command-line arguments or .env file
    API_HOST = api_host or os.getenv("API_HOST")
    API_PORT = api_port or os.getenv("API_PORT")
    API_TOKEN = api_token or os.getenv("API_TOKEN")

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
    dump(directory)


if __name__ == "__main__":
    main()
