from lxml import etree
import requests
from typing import Generator, Optional, Union


class Request:
    url = ""
    headers: dict[str, str] = {}

    @classmethod
    def parse_xml(cls, response_xml: str) -> "etree._Element":
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

        return result_element

    @classmethod
    def post(cls, name: str = "version", args: Optional[list] = None) -> "etree._Element":
        if args is None:
            argstr = ""
        else:
            argstr = "<args>" + "".join(f"<{arg[0]}>{arg[1]}</{arg[0]}>" for arg in args) + "</args>"

        payload = f"""
            <request>
                <service name="{name}">{argstr}</service>
            </request>"""

        response = requests.post(cls.url, headers=cls.headers, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        try:
            return cls.parse_xml(response.text)
        except ValueError:
            raise ValueError(f'Unexpected response from "{payload}" of "{response.text}"')


class Asset(Request):
    @classmethod
    def query_name(cls, name: str) -> Union["Asset", "Collection"]:
        """Finds the newest asset with the given name"""
        rv = cls.post("asset.query", [("where", f"name = '{name}'"), ("action", "get-meta")])
        assets = rv.xpath("./asset")
        asset = sorted(
            assets,
            key=lambda obj: int(obj.xpath("./ctime/@millisec")[0]),
        )[-1]
        a = cls.from_xml(asset)
        if a.is_collection:
            return Collection(a.id)
        return a

    @classmethod
    def from_xml(cls, xml_obj: "etree._Element") -> "Asset":
        obj = cls(xml_obj.get("id"))
        obj._data = xml_obj

        return obj

    def __init__(self, id: Optional[str]) -> None:
        self.id = id
        self._data: Optional["etree._Element"] = None

    @property
    def is_collection(self) -> bool:
        c = self.data.get("collection")
        return c == "true"

    @property
    def has_exif(self) -> bool:
        exif = self.data.xpath("./meta/mf-image-exif")
        return len(exif) > 0

    @property
    def extension(self) -> str:
        ext = self.data.xpath("./name/@ext")
        return "" if len(ext) == 0 else ext[0]

    @property
    def mimetype(self) -> str:
        ty = self.data.xpath("./content/type/text()")
        return "" if len(ty) == 0 else ty[0]

    @property
    def name(self) -> str:
        name = self.data.find("name")
        return "" if name is None else name.text

    @property
    def type(self) -> str:
        ty = self.data.find("type")
        return "" if ty is None else ty.text

    @property
    def data(self):
        if self._data is None:
            r = self.post("asset.get", [("id", self.id)])
            self._data = None if r is None else r.getchildren()[0]
        return self._data


class Collection(Asset):
    def __init__(self, id: Optional[str]) -> None:
        self._assets: Optional[list] = None
        super().__init__(id)

    @property
    def count(self) -> int:
        rv = self.post("asset.collection.members.count", [("id", self.id)])
        return int(rv.xpath("./count/text()")[0])

    @property
    def members(self) -> Generator[str, None, None]:
        for ix in range(0, self.count, 1000):
            rv = self.post(
                "asset.collection.members",
                [("id", self.id), ("size", 1000), ("idx", ix + 1)],
            )
            ids = rv.xpath("./id/text()")
            for id in ids:
                yield id

    @property
    def assets(self) -> Generator[Asset, None, None]:
        for ix in range(0, self.count, 1000):
            print(f"-------{ix}")
            rv = self.post(
                "asset.collection.members",
                [("id", self.id), ("size", 1000), ("idx", ix + 1)],
            )
            ids = rv.xpath("./id/text()")
            if len(ids) > 0:
                try:
                    assets = self.post("asset.get", [("id", id) for id in ids])
                    for a in assets.getchildren():
                        yield Asset.from_xml(a)
                except ValueError:
                    # mediaflux is spitting errors on assets that it lists exist...
                    for id in ids:
                        try:
                            assets = self.post("asset.get", [("id", id)])
                        except ValueError:
                            print(f"FAIL: {id}")
                            continue
                        yield Asset.from_xml(assets.getchildren()[0])


class Server(Request):
    def __init__(self) -> None:
        self._version: Optional[dict] = None

    @property
    def version(self) -> dict:
        if self._version is None:
            self._version = {child.tag: child.text for child in self.post("server.version")}

        return self._version
