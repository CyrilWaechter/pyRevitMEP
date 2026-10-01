"""Serialization for stored patterns: JSON with a legacy Python-dict fallback.

Pure Python: no Revit or pyRevit imports, so it is unit-tested locally.
"""

import ast
import json


def encode_patterns(patterns):
    cleaned = {key: value for key, value in patterns.items() if value}
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True)


def decode_patterns(text):
    if isinstance(text, bytes):
        try:
            text = text.decode("utf8")
        except UnicodeDecodeError:
            return {}
    if not text or not isinstance(text, str):
        return {}
    data = None
    try:
        data = json.loads(text)
    except ValueError:
        try:
            data = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str) and value}


def normalize_config_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf8")
        except UnicodeDecodeError:
            return ""
    if value is None:
        return ""
    return str(value)


def resolve_pattern_sources(entity_text, legacy_patterns, config_patterns, defaults):
    """Return (patterns, source) following the storage precedence.

    A non-empty entity text means the model storage is authoritative even when it
    decodes to an empty dict (the user explicitly saved nothing); only a missing or
    invalid entity falls back to the legacy parameter, then the user config, then the
    built-in defaults.
    """
    if entity_text:
        return decode_patterns(entity_text), "model"
    if legacy_patterns:
        return legacy_patterns, "legacy"
    if config_patterns:
        return config_patterns, "config"
    return dict(defaults), "defaults"
