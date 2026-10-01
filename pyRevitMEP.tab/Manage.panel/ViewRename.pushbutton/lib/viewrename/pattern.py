"""Rename-pattern mini-language: `name(Parameter Name)`, `bip(BUILTIN_NAME)`, `Guid('...')`.

Pure Python: no Revit or pyRevit imports, so it is unit-tested locally.
"""

import re

NAME_RE = re.compile(r"name\(([^)]+)\)")
BIP_RE = re.compile(r"bip\((\w+)\)")
GUID_RE = re.compile(r"""Guid\(\s*['"]([0-9a-fA-F-]{36})['"]\s*\)""")
KNOWN_REFERENCES = ("name(", "bip(", "Guid(")
REFERENCE_REGEXES = ((NAME_RE, "name"), (BIP_RE, "bip"), (GUID_RE, "guid"))


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
    for match in re.finditer(r"[A-Za-z_]\w*\(", pattern):
        word = match.group(0)
        if not any(word.endswith(known) for known in KNOWN_REFERENCES):
            errors.append(f"Unknown reference: {word}")
    for match in re.finditer(r"Guid\(", pattern):
        if not GUID_RE.match(pattern, match.start()):
            errors.append("Invalid Guid reference")
    return errors


def tokenize(text):
    """Split a pattern into ordered (kind, value) segments.

    kind is "text", "name", "bip" or "guid"; value is the literal text or the
    exact reference substring, so join_tokens() is lossless.
    """
    segments = []
    position = 0
    for start, end, kind, value in reference_matches(text):
        if start > position:
            segments.append(("text", text[position:start]))
        segments.append((kind, value))
        position = end
    if position < len(text):
        segments.append(("text", text[position:]))
    return segments


def reference_matches(text):
    """Return non-overlapping (start, end, kind, value) reference matches."""
    matches = []
    for regex, kind in REFERENCE_REGEXES:
        for match in regex.finditer(text):
            matches.append((match.start(), match.end(), kind, match.group(0)))
    matches.sort()
    result = []
    last_end = 0
    for start, end, kind, value in matches:
        if start >= last_end:
            result.append((start, end, kind, value))
            last_end = end
    return result


def join_tokens(segments):
    return "".join(value for _, value in segments)
