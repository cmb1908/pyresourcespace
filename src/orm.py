from lxml import etree
import requests
from typing import Generator, Optional

import xml


class Request:
    url = ""
    headers: dict[str, str] = {}

    def parse_xml(self, response_xml: str) -> dict:
        """
        Parses the given XML string, returning the <result> content if <reply type="result"> is found.
        Raises an exception if the <reply> type is not "result".

        Args:
            response_xml (str): The XML string to parse.

        Returns:
            dict: A dictionary representation of the <result> content.

        Raises:
            ValueError: If the <reply> type is not "result".
        """
        # Convert the XML string to bytes to handle encoding declarations
        response_bytes = response_xml.encode("utf-8")

        # Parse the XML response
        root = etree.fromstring(response_bytes)

        # Find the <reply> element
        reply_element = root.find("reply")
        if reply_element is None:
            raise ValueError("No <reply> element found in the response.")

        # Get the type attribute of <reply>
        reply_type = reply_element.get("type")
        if reply_type == "error":
            m = reply_element.find("message")
            raise ValueError(f"Call failed: {'None' if m is None else m.text}")
        if reply_type != "result":
            raise ValueError(f"Unexpected reply type: {reply_type} ({response_xml})")

        # Convert the <result> element into a dictionary
        result_element = reply_element.find("result")
        if result_element is None:
            raise ValueError("No <result> element found in the reply.")

        return xml.etree_to_dict(result_element)

    def post(self, name: str = "version", args: Optional[list] = None) -> dict:
        if args is None:
            argstr = ""
        else:
            argstr = "<args>" + "".join(f"<{arg[0]}>{arg[1]}</{arg[0]}>" for arg in args) + "</args>"

        payload = f"""
            <request>
                <service name="{name}">{argstr}</service>
            </request>"""

        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        try:
            return self.parse_xml(response.text)
        except ValueError:
            raise ValueError(f'Unexpected response from "{payload}" of "{response.text}"')


class Asset(Request):
    def __init__(self, id: str) -> None:
        self.id = id
        self._data: Optional[dict] = None

    @classmethod
    def from_data(cls, xml_data: dict) -> "Asset":
        try:
            obj = cls(xml_data["_attributes"]["id"])
        except:
            print(xml_data)
        obj._data = xml_data

        return obj

    @property
    def is_collection(self) -> bool:
        return self.data["_attributes"].get("collection") == "true"

    @property
    def has_exif(self) -> bool:
        return self.data.get("meta", {}).get("mf-image-exif") is not None

    @property
    def extension(self) -> str:
        if type(self.data["name"]) is str:
            return ""
        return self.data["name"]["_attributes"]["ext"]

    @property
    def name(self) -> str:
        return self.data["name"] if type(self.data["name"]) is str else self.data["name"]["text"]

    @property
    def type(self) -> str:
        return self.data.get("type")

    @property
    def data(self):
        if self._data is None:
            self._data = self.post("asset.get", [("id", self.id)])["asset"]
        return self._data


class Collection(Request):
    def __init__(self, id: str) -> None:
        self.id = id
        self._assets: Optional[list] = None

    @property
    def count(self) -> int:
        return int(self.post("asset.collection.members.count", [("id", self.id)])["count"])

    @property
    def members(self) -> Generator[str, None, None]:
        for ix in range(0, self.count, 1000):
            m = self.post(
                "asset.collection.members",
                [("id", self.id), ("size", 1000), ("idx", ix + 1)],
            )
            if type(m) is str or m.get("id") is None:
                break
            if type(m["id"]) is str:
                yield m["id"]
            else:
                for id in m["id"]:
                    yield id

    @property
    def assets(self) -> Generator[Asset, None, None]:
        for ix in range(0, self.count, 1000):
            print(f"-------{ix}")
            m = self.post(
                "asset.collection.members",
                [("id", self.id), ("size", 1000), ("idx", ix + 1)],
            )
            if type(m) is str or m.get("id") is None:
                break
            if type(m["id"]) is str:
                yield Asset(m["id"])
            else:
                try:
                    assets = self.post("asset.get", [("id", id) for id in m["id"]])["asset"]
                    for a in assets:
                        yield Asset.from_data(a)
                except ValueError:
                    # mediaflux is spitting errors on assets that it lists exist...
                    for id in m["id"]:
                        try:
                            asset = self.post("asset.get", [("id", id)])["asset"]
                        except ValueError:
                            print(f"FAIL: {id}")
                            continue
                        yield Asset.from_data(asset)


class Server(Request):
    def __init__(self) -> None:
        self._version: Optional[dict] = None

    @property
    def version(self) -> dict:
        if self._version is None:
            self._version = self.post("server.version")

        return self._version
