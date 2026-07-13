#!/bin/sh
# Refresh the iOS client's OpenAPI schema from production.
#
# Normalizes Pydantic's OpenAPI 3.1 nullable style (anyOf: [X, {type: null}])
# down to X, because swift-openapi-generator does not support the standalone
# "null" schema type and silently skips such properties (note, city, date).
# Optionality is preserved: the fields are absent from "required".
set -eu

cd "$(dirname "$0")"

curl -fsS https://unwelts-api.fly.dev/openapi.json | python3 -c '
import json, sys

NULL_SCHEMA = {"type": "null"}


def is_nullable(schema):
    return isinstance(schema, dict) and NULL_SCHEMA in schema.get("anyOf", [])


def strip_null(node):
    if isinstance(node, dict):
        # A JSON-null-able field must not be "required": Swift then decodes
        # it via decodeIfPresent, which maps an explicit null to nil instead
        # of crashing on a non-optional String.
        properties = node.get("properties")
        if isinstance(properties, dict) and isinstance(node.get("required"), list):
            node["required"] = [
                name for name in node["required"] if not is_nullable(properties.get(name))
            ]
        any_of = node.get("anyOf")
        if isinstance(any_of, list):
            non_null = [s for s in any_of if s != NULL_SCHEMA]
            if len(non_null) == 1 and len(non_null) != len(any_of):
                del node["anyOf"]
                for key, value in non_null[0].items():
                    node.setdefault(key, value)
        for value in node.values():
            strip_null(value)
    elif isinstance(node, list):
        for value in node:
            strip_null(value)

spec = json.load(sys.stdin)
strip_null(spec)
json.dump(spec, sys.stdout, indent=1)
' > Unwelts/Unwelts/openapi.json

echo "openapi.json refreshed and normalized"
