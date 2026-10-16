"""Small offline JSON-Schema subset used for Foundation contract checks."""

import json
import re
from pathlib import Path

from .errors import ContractError


TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def validate_instance(instance, schema, path="$ ", resolver=None):
    path = path.strip()
    if "$ref" in schema:
        if resolver is None:
            raise ContractError("%s cannot resolve %s" % (path, schema["$ref"]))
        return validate_instance(instance, resolver(schema["$ref"]), path, resolver)
    expected = schema.get("type")
    if expected:
        valid = TYPE_MAP[expected]
        if not isinstance(instance, valid) or expected in {"integer", "number"} and isinstance(instance, bool):
            raise ContractError("%s must be %s" % (path, expected))
    if "enum" in schema and instance not in schema["enum"]:
        raise ContractError("%s must be one of %s" % (path, schema["enum"]))
    if "const" in schema and instance != schema["const"]:
        raise ContractError("%s must equal %r" % (path, schema["const"]))
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            raise ContractError("%s is shorter than minLength" % path)
        if schema.get("pattern") and not re.search(schema["pattern"], instance):
            raise ContractError("%s does not match its required pattern" % path)
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ContractError("%s is less than its minimum" % path)
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise ContractError("%s.%s is required" % (path, key))
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(instance) - set(properties)
            if unknown:
                raise ContractError("%s has unknown fields: %s" % (path, sorted(unknown)))
        for key, child in properties.items():
            if key in instance:
                validate_instance(instance[key], child, "%s.%s" % (path, key), resolver)
    if isinstance(instance, list) and "items" in schema:
        if len(instance) < schema.get("minItems", 0):
            raise ContractError("%s has fewer items than required" % path)
        for index, child in enumerate(instance):
            validate_instance(child, schema["items"], "%s[%d]" % (path, index), resolver)
    return instance


def load_schema(schema_root, name):
    path = Path(schema_root) / (name + ".schema.json")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_named(instance, schema_root, name):
    def resolver(reference):
        if not reference.endswith(".schema.json") or "/" in reference or "\\" in reference:
            raise ContractError("unsupported schema reference %s" % reference)
        return load_schema(schema_root, reference.replace(".schema.json", ""))

    return validate_instance(instance, load_schema(schema_root, name), resolver=resolver)
