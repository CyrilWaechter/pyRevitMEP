import os
import pathlib
import urllib.request
from typing import Optional
from lxml import etree

MATERIALSDBINDEXURL = "http://www.materialsdb.org/download/ProducerIndex.xml"


def get_cache_folder():
    cache_dir = pathlib.Path(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CACHE_HOME")
        or pathlib.Path.home() / ".cache"
    ).joinpath(
        "materialsdb",
    )
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cached_index_path() -> pathlib.Path:
    return get_cache_folder() / "ProducerIndex.xml"


def parse_cached_index() -> etree._ElementTree:
    path = get_cached_index_path()
    if path.exists():
        return etree.parse(str(path))
    root = etree.Element("root")
    return etree.ElementTree(root)


def get_by_id(root: etree._Element, id: str) -> Optional[etree._Element]:
    for company in root:
        if company.get("id") == id:
            return company
    return None


def require_update(cached_company, company) -> bool:
    if cached_company is None:
        return True
    for attrib in ["LastKnownDate", "KnownVersion"]:
        if company.get(attrib) > cached_company.get(attrib):
            return True
    return False


def get_producers_dir() -> pathlib.Path:
    producer_path = get_cache_folder().joinpath("Producers")
    pathlib.Path(producer_path).mkdir(parents=True, exist_ok=True)
    return producer_path


def update_producers_data():
    cached_index = parse_cached_index()
    cached_root = cached_index.getroot()
    new_index = etree.parse(MATERIALSDBINDEXURL)
    new_root = new_index.getroot()
    producers_dir = get_producers_dir()
    has_index_update = False
    for company in new_root:
        cached_company = get_by_id(cached_root, company.get("id"))
        if (
            not require_update(cached_company, company)
            and (producers_dir / pathlib.Path(company.get("href")).name).exists()
        ):
            continue
        if cached_company:
            (producers_dir / pathlib.Path(cached_company.get("href")).name).unlink(True)
        has_index_update = True
        producer_path = producers_dir / pathlib.Path(company.get("href")).name
        urllib.request.urlretrieve(company.get("href"), producer_path)
    if has_index_update:
        new_index.write(str(get_cached_index_path()))


def producers():
    for producer in get_producers_dir().iterdir():
        if producer.suffix.lower() == ".xml":
            yield producer


def main():
    update_producers_data()


if __name__ == "__main__":
    main()
