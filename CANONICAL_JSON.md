# Canonical JSON

AECP computes semantic digests using this deterministic representation:

1. UTF-8 encoding;
2. object keys sorted by Python Unicode code-point order;
3. arrays retained in authored order;
4. separators `,` and `:` with no added whitespace;
5. JSON booleans and null in their standard lowercase form;
6. NaN and Infinity prohibited;
7. no Unicode ASCII-escaping requirement (`ensure_ascii=false`);
8. duplicate object keys rejected at parse time.

Reference expression:

```python
json.dumps(value, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
```

`content_sha256` and `fixture_canonical_sha256` are lowercase hexadecimal SHA-256 digests of these bytes.

This v0.1 representation is the exact Python-compatible algorithm above; it is not asserted to be RFC 8785. Published fixtures/results avoid floating-point values so cross-language ports do not need to reproduce language-specific float rendering.
