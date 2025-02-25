import copy
from lxml import etree
import requests
from typing import Generator, Optional, Union, cast
from xml.sax.saxutils import escape


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
    def post(
        cls,
        name: str,
        args: Optional[list[tuple]] = None,
        xml: Optional[list["etree._Element"]] = None,
    ) -> "etree._Element":
        argstr = ""
        if args is not None or xml is not None:
            argstr = "<args>"
            if args is not None:
                argstr += "".join(f"<{arg[0]}>{arg[1]}</{arg[0]}>" for arg in args)
            if xml is not None:
                argstr += "".join(etree.tostring(x, encoding="utf-8").decode("utf-8") for x in xml)
            argstr += "</args>"

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

    @property
    def data(self) -> "etree._Element":
        """Abstract property that must be implemented in subclasses."""
        return cast("etree._Element", None)

    def export(self, fn: str) -> None:
        with open(fn, "wb") as f:
            f.write(etree.tostring(self.data, pretty_print=True, encoding="utf-8", xml_declaration=True))


class Namespace(Request):
    @classmethod
    def filter_spaces(cls) -> list["Namespace"]:
        """Returns a list of filter namespaces"""
        rv = cls.post("asset.filter.namespace.list")
        return [cls(x) for x in rv.xpath("./namespace/text()")]

    @classmethod
    def from_xml(cls, xml_obj: "etree._Element") -> "Namespace":
        obj = cls(xml_obj.get("name"))
        obj._data = xml_obj

        return obj

    def __init__(self, namespace: Optional[str] = None) -> None:
        self.namespace = namespace
        self._data: Optional["etree._Element"] = None
        self._filters: Optional["etree._Element"] = None

    @property
    def label(self) -> str:
        val = self.data.xpath("./label/text()")
        return "" if len(val) == 0 else val[0]

    @property
    def data(self) -> "etree._Element":
        if self._data is None:
            r = self.post("asset.filter.namespace.describe", [("namespace", self.namespace)])
            self._data = None if r is None else r.getchildren()[0]
        return self._data

    @property
    def filters(self):
        if self._filters is None:
            r = self.post("asset.filter.list", [("namespace", self.namespace)])
            self._filters = None if r is None else [Filter(self.namespace, x) for x in r.xpath("./filter/text()")]
        return self._filters

    @property
    def exists(self) -> bool:
        r = self.post(
            "asset.filter.namespace.exists",
            [("namespace", self.namespace)],
        )
        return r.xpath("./exists/text()") == ["true"]

    def destroy(self) -> None:
        if self.exists:
            self.post(
                "asset.filter.namespace.destroy",
                [("namespace", self.namespace)],
            )

    def create(self) -> None:
        self.destroy()

        self.post(
            "asset.filter.namespace.create",
            [("namespace", self.namespace)],
            self.data.getchildren(),
        )


class FilterArg:
    def __init__(self, xml_obj: "etree._Element") -> None:
        self.data = xml_obj

    @property
    def name(self) -> str:
        name = self.data.xpath("./name/text()")
        return "" if len(name) == 0 else name[0]

    @property
    def description(self) -> str:
        desc = self.data.xpath("./description/text()")
        return "" if len(desc) == 0 else desc[0]

    @property
    def label(self) -> str:
        label = self.data.xpath("./label/text()")
        return "" if len(label) == 0 else label[0]

    @property
    def type(self) -> str:
        ty = self.data.xpath("./type/name/text()")
        return "" if len(ty) == 0 else ty[0]

    @property
    def restrictions(self) -> dict[str, str]:
        restrictions = self.data.xpath("./type/restriction/value")
        return {r.get("description"): r.text for r in restrictions}


class Filter(Request):
    @classmethod
    def from_xml(cls, xml_obj: "etree._Element") -> "Filter":
        obj = cls(xml_obj.get("namespace"), xml_obj.get("name"))
        obj._data = xml_obj

        return obj

    def __init__(self, namespace: Optional[str] = None, name: Optional[str] = None) -> None:
        self.namespace = namespace
        self.name = name
        self._data: Optional["etree._Element"] = None
        self._args: Optional[list["FilterArg"]] = None

    @property
    def description(self) -> str:
        desc = self.data.xpath("./description/text()")
        return "" if len(desc) == 0 else desc[0]

    @property
    def label(self) -> str:
        label = self.data.xpath("./label/text()")
        return "" if len(label) == 0 else label[0]

    @property
    def args(self) -> list["FilterArg"]:
        if self._args is None:
            self._args = [FilterArg(x) for x in self.data.xpath("./arg")]
        return cast(list["FilterArg"], self._args)

    @property
    def data(self) -> "etree._Element":
        if self._data is None:
            r = self.post(
                "asset.filter.describe",
                [("namespace", self.namespace), ("name", self.name)],
            )
            self._data = None if r is None else r.getchildren()[0]
        return self._data

    @property
    def exists(self) -> bool:
        r = self.post(
            "asset.filter.exists",
            [("namespace", self.namespace), ("name", self.name)],
        )
        return r.xpath("./exists/text()") == ["true"]

    def destroy(self) -> None:
        if self.exists:
            self.post(
                "asset.filter.destroy",
                [("namespace", self.namespace), ("name", self.name)],
            )

    def create(self) -> None:
        self.destroy()

        # Need to transform <type>
        xargs = copy.deepcopy(self.data)

        def transform_type_elements(root):
            """
            Modifies all <type> elements in the given XML tree:
            - Moves <name> value to an attribute "type"
            - Removes the <name> element

            :param root: lxml.etree._Element (Root of the XML document)
            """
            for type_elem in root.findall(".//type"):  # Find all <type> elements
                name_elem = type_elem.find("name")  # Find the <name> element inside <type>
                if name_elem is not None:
                    type_value = name_elem.text.strip() if name_elem.text else ""
                    type_elem.set("type", type_value)  # Set as attribute
                    type_elem.remove(name_elem)  # Remove <name> element

                # Check if <type> has no remaining child elements
                if not list(type_elem):
                    type_elem.text = None

        transform_type_elements(xargs)

        self.post(
            "asset.filter.create",
            [("namespace", self.namespace), ("name", self.name)],
            xargs.getchildren(),
        )

    def query_str(self, *args, **kwargs):
        def e(v):
            return escape(v, {'"': "&quot;", "'": "&apos;"}) if type(v) is str else v

        args = ",".join(f"{e(k)}=\\'{e(v)}\\'" for k, v in kwargs.items())
        return f"filter '{self.namespace}:{self.name}({args})'"


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
    def query(cls, query: str) -> list[Union["Asset", "Collection"]]:
        """Finds a list of assets matching the given query"""
        qr = cls.post("asset.query", [("where", query), ("action", "get-meta")])

        assets = qr.xpath("./asset")
        rv: list[Union["Asset", "Collection"]] = []
        for asset in assets:
            a = cls.from_xml(asset)
            if a.is_collection:
                rv.append(Collection(a.id))
            else:
                rv.append(a)
        return rv

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

    def checksum(self, base: int = 10) -> str:
        cs = self.data.xpath(f"./content/csum[@base='{base}']")
        return "" if len(cs) == 0 else cs[0]

    @property
    def extension(self) -> str:
        ext = self.data.xpath("./name/@ext")
        return "" if len(ext) == 0 else ext[0]

    @property
    def mf_name(self) -> str:
        val = self.data.xpath("./meta/mf-name/name/text()")
        return "" if len(val) == 0 else val[0]

    @property
    def mf_source_name(self) -> str:
        val = self.data.xpath("./meta/mf-source-name/name/text()")
        return "" if len(val) == 0 else val[0]

    @property
    def mimetype(self) -> str:
        ty = self.data.xpath("./content/type/text()")
        return "" if len(ty) == 0 else ty[0]

    @property
    def name(self) -> str:
        name = self.data.find("name")
        return "" if name is None else cast(str, name.text)

    @property
    def parent(self) -> str:
        parent = self.data.find("parent")
        return "" if parent is None else cast(str, parent.text)

    @property
    def type(self) -> str:
        ty = self.data.find("type")
        return "" if ty is None else cast(str, ty.text)

    @property
    def data(self) -> "etree._Element":
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
    def count_all(self) -> int:
        rv = self.post(
            "asset.collection.members.count",
            [("id", self.id), ("include-subcollections", "true")],
        )
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

    def get_assets(self, get_all=False) -> Generator[Asset, None, None]:
        for ix in range(0, self.count, 1000):
            args = [("id", self.id), ("size", 1000), ("idx", ix + 1)]
            if get_all:
                args.append(("include-subcollections", "true"))
            rv = self.post("asset.collection.members", args)
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

    @property
    def assets(self) -> Generator[Asset, None, None]:
        return self.get_assets()

    @property
    def assets_all(self) -> Generator[Asset, None, None]:
        return self.get_assets(True)


class Server(Request):
    def __init__(self) -> None:
        self._version: Optional[dict] = None

    @property
    def version(self) -> dict:
        if self._version is None:
            self._version = {child.tag: child.text for child in self.post("server.version")}

        return self._version
