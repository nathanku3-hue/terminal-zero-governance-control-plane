#!/usr/bin/env python3
"""Validate research high-confidence claims against source text evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys


def words_count(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def load_claims(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("claims JSON must be a list")
    flattened: list[dict] = []
    for item in data:
        if isinstance(item, list):
            for nested in item:
                if not isinstance(nested, dict):
                    raise ValueError("claims JSON entries must be objects")
                flattened.append(nested)
        else:
            if not isinstance(item, dict):
                raise ValueError("claims JSON entries must be objects")
            flattened.append(item)
    return flattened


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims-json", required=True)
    parser.add_argument("--max-quoted-words", type=int, default=20)
    parser.add_argument("--max-paraphrased-words", type=int, default=30)
    args = parser.parse_args()

    try:
        claims = load_claims(args.claims_json)
        high_claims = [
            c
            for c in claims
            if str(c.get("confidence", "high")).strip().lower() == "high"
        ]
        if not high_claims:
            raise ValueError("No high-confidence claims found")

        cited = 0
        for claim in high_claims:
            claim_id = str(claim.get("claim_id", "")).strip()
            source_id = str(claim.get("source_id", "")).strip()
            source_locator = str(claim.get("source_locator", "")).strip()
            source_text_path = str(claim.get("source_text_path", "")).strip()
            support_strength = str(claim.get("support_strength", "")).strip()
            snippet = str(claim.get("evidence_snippet", "")).strip()
            snippet_type = str(claim.get("snippet_type", "paraphrased")).strip().lower()

            if not claim_id:
                raise ValueError("Missing claim_id")
            if not source_id or not source_locator:
                raise ValueError(f"{claim_id}: missing source_id or source_locator")
            cited += 1
            if support_strength.lower() != "direct":
                raise ValueError(f"{claim_id}: support_strength must be Direct for high confidence")
            if not snippet:
                raise ValueError(f"{claim_id}: evidence_snippet is missing")

            wc = words_count(snippet)
            if snippet_type == "quoted":
                if wc > args.max_quoted_words:
                    raise ValueError(f"{claim_id}: quoted snippet too long ({wc} words)")
            else:
                if wc > args.max_paraphrased_words:
                    raise ValueError(f"{claim_id}: paraphrased snippet too long ({wc} words)")

            if not source_text_path:
                raise ValueError(f"{claim_id}: source_text_path is missing")
            with open(source_text_path, "r", encoding="utf-8") as handle:
                source_text = handle.read()

            if normalize(snippet) not in normalize(source_text):
                raise ValueError(f"{claim_id}: snippet not found in source_text_path")

        print(
            "VALID: "
            f"claims_total={len(high_claims)} claims_cited={cited}"
        )
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as err:
        print(f"INVALID: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
