"""Rename-pattern mini-language: `name(Parameter Name)`, `bip(BUILTIN_NAME)`, `Guid('...')`.

Pure Python: no Revit or pyRevit imports, so it is unit-tested locally.
"""

import re

NAME_RE = re.compile(r"name\(([^)]+)\)")
BIP_RE = re.compile(r"bip\((\w+)\)")
GUID_RE = re.compile(r"""Guid\(\s*['"]([0-9a-fA-F-]{36})['"]\s*\)""")
REFERENCE_WORD_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]\w*\(")
KNOWN_REFERENCES = ("name(", "bip(", "Guid(")


class Resolver:
    """Duck-typed interface: by_name/by_bip/by_guid return a string, "" when absent."""

    def by_name(self, name):
        raise NotImplementedError

    def by_bip(self, name):
        raise NotImplementedError

    def by_guid(self, guid):
        raise NotImplementedError


def apply_pattern(pattern, resolver):
    result = NAME_RE.sub(lambda match: resolver.by_name(match.group(1)), pattern)
    result = GUID_RE.sub(lambda match: resolver.by_guid(match.group(1)), result)
    return BIP_RE.sub(lambda match: resolver.by_bip(match.group(1)), result)


def validate_pattern(pattern):
    errors = []
    if pattern.count("(") != pattern.count(")"):
        errors.append("Unbalanced parentheses")
    for match in REFERENCE_WORD_RE.finditer(pattern):
        word = match.group(0)
        if word not in KNOWN_REFERENCES:
            errors.append(f"Unknown reference: {word}")
    return errors
