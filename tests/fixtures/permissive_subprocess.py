#!/usr/bin/env python3
"""Harmless one-request/one-response JSON-lines adapter for tests."""

import json
import sys


request = json.loads(sys.stdin.readline())
response = {
    "decision": "ALLOW",
    "reason": "test_subprocess_permissive",
    "emissions": request["synthetic_effect"]["entries"],
}
sys.stdout.write(json.dumps(response, sort_keys=True) + "\n")
