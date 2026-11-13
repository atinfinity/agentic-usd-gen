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


def _nodes(schema):
    yield schema
    for v in schema.values():
        for s in v if isinstance(v, list) else [v]:
            if isinstance(s, dict):
                yield from _nodes(s)


def test_schemas_fit_api_limits():
    """構造化出力が受け付けない書き方をしていない（anyOf は 16 個まで、数値の範囲は不可）。"""
    from agentic_usd_gen import vision, visual_check

    for schema in (search.SCHEMA, vision.SCHEMA, visual_check.SCHEMA):
        nodes = list(_nodes(schema))
        assert sum("anyOf" in n or isinstance(n.get("type"), list) for n in nodes) <= 16
        for n in nodes:
            assert not {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"} & set(n)


def test_normalize_restores_none():
    data = {
        "notes": " ", "container_material": "",
        "image_candidates": [{"url": "u", "source_page": "", "description": "正面"}],
        "sources": [{"url": "u", "note": ""}],
        "parts": [{"material": "", "faces": [0, -1, -1, -1, 2, -1]},
                  {"material": "wood", "faces": []},
                  {"material": "metal", "faces": [-1, -1, -1, -1, -1, -1]},
                  {"material": "paper", "faces": [1]}],
    }
    out = search._normalize(data)
    assert out["notes"] is None and out["container_material"] is None
    assert out["image_candidates"][0] == {"url": "u", "source_page": None, "description": "正面"}
    assert out["sources"][0]["note"] is None
    assert out["parts"][0]["material"] is None
    assert out["parts"][0]["faces"] == {"front": 0, "right": None, "back": None, "left": None, "top": 2, "bottom": None}
    assert out["parts"][1] == {"material": "wood", "faces": None}
    assert out["parts"][2]["faces"] is None
    assert out["parts"][3]["faces"] == {"front": 1, "right": None, "back": None, "left": None, "top": None, "bottom": None}


def test_ratio_out_of_range_is_dropped():
    from agentic_usd_gen.vision import _ratio

    assert _ratio(0.25) == 0.25 and _ratio(0) == 0 and _ratio(1) == 1
    assert _ratio(None) is None and _ratio(1.2) is None and _ratio(-0.1) is None
