import os
import pathlib
import urllib.request
from collections import namedtuple
from typing import Optional
from lxml import etree

MATERIALSDBINDEXURLLIST = [
    "http://www.materialsdb.org/download/ProducerIndex.xml",
    "http://www.materialsdb.org/download/generic/GenericIndex.xml",
]


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


def get_cached_index_path(index) -> pathlib.Path:
    return get_cache_folder() / pathlib.Path(index).name


def parse_cached_index(index) -> etree._ElementTree:
    path = get_cached_index_path(index)
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


Report = namedtuple("Report", ["existing", "updated", "deleted"])


def update_producers_data(url_list=MATERIALSDBINDEXURLLIST):
    existing = []
    updated = []
    deleted = []
    for index in url_list:
        report = update_producers_from_index(index)
        existing.extend(report.existing)
        updated.extend(report.updated)
        deleted.extend(report.deleted)
    return Report(existing, updated, deleted)


def update_producers_from_index(index):
    cached_index = parse_cached_index(index)
    cached_root = cached_index.getroot()
    new_index = etree.parse(index)
    new_root = new_index.getroot()
    producers_dir = get_producers_dir()
    has_index_update = False
    existing = []
    updated = []
    deleted = []
    for company in new_root:
        cached_producer = get_by_id(cached_root, company.get("id"))
        producer_path = producers_dir / pathlib.Path(company.get("href")).name
        if not require_update(cached_producer, company) and producer_path.exists():
            existing.append(producer_path)
            continue
        if cached_producer:
            cached_path = producers_dir / pathlib.Path(cached_producer.get("href")).name
            deleted.append(cached_path)
            cached_path.unlink(True)
        has_index_update = True
        urllib.request.urlretrieve(company.get("href"), producer_path)
        updated.append(producer_path)
    if has_index_update:
        new_index.write(str(get_cached_index_path(index)))
    return Report(existing, updated, deleted)


def producers():
    for producer in get_producers_dir().iterdir():
        if producer.suffix.lower() == ".xml":
            yield producer


def main():
    update_producers_data()


if __name__ == "__main__":
    main()
