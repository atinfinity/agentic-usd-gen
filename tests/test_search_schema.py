from agentic_usd_gen import search


def _walk(schema, path="$"):
    if "anyOf" in schema:
        for s in schema["anyOf"]:
            yield from _walk(s, path)
        return
    if schema.get("type") == "object":
        yield path, schema
        for k, s in schema["properties"].items():
            yield from _walk(s, f"{path}.{k}")
    elif schema.get("type") == "array":
        yield from _walk(schema["items"], f"{path}[]")


def test_schema_is_strict():
    for path, obj in _walk(search.SCHEMA):
        assert obj.get("additionalProperties") is False, path
        assert set(obj["required"]) == set(obj["properties"]), path


def test_schema_matches_spec():
    from agentic_usd_gen.spec import ProductSpec

    props = set(search.SCHEMA["properties"])
    assert {"product_name", "slug", "shape_class", "dimensions"} <= props
    assert props <= set(ProductSpec.__dataclass_fields__)
