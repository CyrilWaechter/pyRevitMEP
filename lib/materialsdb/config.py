import os
import pathlib
import json
from typing import Dict


def get_config_dir():
    config_dir = pathlib.Path(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CACHE_HOME")
        or pathlib.Path.home() / ".config"
    ).joinpath(
        "materialsdb",
    )
    pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)
    return config_dir


def get_base_config_path() -> pathlib.Path:
    return get_config_dir() / "config.json"


def get_base_config() -> Dict[str, str]:
    base_config_path = get_base_config_path()
    if base_config_path.exists():
        return json.loads(get_base_config_path().read_text("utf-8"))
    return {"lang": "fr", "country": "CH"}


def get_param(param: str) -> str:
    return get_base_config()[param]


def set_param(param: str, value: str) -> None:
    config = get_base_config()
    config[param] = value
    get_base_config_path().write_text(json.dumps(config), encoding="utf-8")


def get_lang() -> str:
    return get_param("lang")


def set_lang(lang: str):
    set_param("lang", lang)


def get_country() -> str:
    return get_param("country")


def set_country(country: str):
    set_param("country", country)


def main():
    lang = get_lang()
    set_lang(lang)
    country = get_country()
    set_country(country)


if __name__ == "__main__":
    main()
