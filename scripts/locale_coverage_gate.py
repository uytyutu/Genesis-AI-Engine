#!/usr/bin/env python3
"""L1 Locale coverage gate — etalon DE/EN/RU/UK catalog parity.

Usage:
  py scripts/locale_coverage_gate.py           # report + exit 1 on fail
  py scripts/locale_coverage_gate.py --fill     # fill missing keys (EN→DE fallback)
  py scripts/locale_coverage_gate.py --json     # machine-readable summary

L1 required namespaces (must be 100% vs DE baseline):
  common, site, order, client, vector, errors

Legacy `chat` is reported but does not fail the gate.
Product terminology file: dashboard/frontend/locales/terminology.json
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
LOCALES = REPO / "dashboard" / "frontend" / "locales"
ETALON = ("de", "en", "ru", "uk")
REQUIRED_NS = ("common", "site", "order", "client", "vector", "errors")
LEGACY_NS = ("chat",)
BASELINE = "de"
PREFERRED_FILL = ("en", "de")


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(val, path))
    else:
        out[prefix] = obj
    return out


def unflatten(flat: dict[str, Any]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    for path, value in flat.items():
        cur = root
        parts = path.split(".")
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value
    return root


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def deep_get(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def deep_set(data: dict[str, Any], path: str, value: Any) -> None:
    cur = data
    parts = path.split(".")
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def load_terminology() -> list[str]:
    raw = load_json(LOCALES / "terminology.json")
    terms = raw.get("terms") or []
    return [str(t) for t in terms if str(t).strip()]


def analyze_ns(ns: str) -> dict[str, Any]:
    baseline_path = LOCALES / BASELINE / f"{ns}.json"
    baseline = load_json(baseline_path)
    base_flat = flatten(baseline)
    result: dict[str, Any] = {
        "namespace": ns,
        "baseline_keys": len(base_flat),
        "locales": {},
        "ok": True,
    }
    if not baseline_path.is_file():
        result["ok"] = False
        result["error"] = f"missing baseline {baseline_path}"
        return result

    for loc in ETALON:
        path = LOCALES / loc / f"{ns}.json"
        data = load_json(path)
        flat = flatten(data)
        missing = sorted(set(base_flat) - set(flat))
        extra = sorted(set(flat) - set(base_flat))
        empty = sorted(
            k
            for k, v in flat.items()
            if isinstance(v, str) and not v.strip()
        )
        # Also empty in baseline for DE
        if loc == BASELINE:
            empty = sorted(
                k
                for k, v in base_flat.items()
                if isinstance(v, str) and not v.strip()
            )
        coverage = (
            100.0
            if not base_flat
            else round(100.0 * (len(base_flat) - len(missing)) / len(base_flat), 2)
        )
        loc_ok = not missing and not empty and path.is_file()
        if not loc_ok:
            result["ok"] = False
        result["locales"][loc] = {
            "keys": len(flat),
            "missing": missing,
            "extra": extra,
            "empty": empty,
            "coverage_pct": coverage,
            "ok": loc_ok,
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
        }
    return result


def fill_ns(ns: str) -> dict[str, int]:
    """Fill missing keys from EN then DE; fix empty strings from EN/DE."""
    baseline = load_json(LOCALES / BASELINE / f"{ns}.json")
    base_flat = flatten(baseline)
    packs = {loc: load_json(LOCALES / loc / f"{ns}.json") for loc in ETALON}
    filled = {loc: 0 for loc in ETALON}

    # Fix empty baseline strings with EN if available, else placeholder
    en_flat = flatten(packs["en"])
    for key, val in list(base_flat.items()):
        if isinstance(val, str) and not val.strip():
            repl = en_flat.get(key)
            if isinstance(repl, str) and repl.strip():
                deep_set(baseline, key, repl)
                base_flat[key] = repl
                filled["de"] += 1
            else:
                placeholder = f"[{key.split('.')[-1]}]"
                deep_set(baseline, key, placeholder)
                base_flat[key] = placeholder
                filled["de"] += 1

    packs["de"] = baseline
    save_json(LOCALES / BASELINE / f"{ns}.json", baseline)
    base_flat = flatten(baseline)

    for loc in ETALON:
        if loc == BASELINE:
            continue
        data = packs[loc] or {}
        flat = flatten(data)
        changed = False
        for key, base_val in base_flat.items():
            cur = flat.get(key)
            needs = key not in flat or (
                isinstance(cur, str) and not cur.strip()
            )
            if not needs:
                continue
            fill_val = None
            for src in PREFERRED_FILL:
                candidate = flatten(packs[src]).get(key)
                if isinstance(candidate, str) and candidate.strip():
                    fill_val = candidate
                    break
                if candidate is not None and not isinstance(candidate, str):
                    fill_val = candidate
                    break
            if fill_val is None or (isinstance(fill_val, str) and not str(fill_val).strip()):
                if isinstance(base_val, str) and base_val.strip():
                    fill_val = base_val
                else:
                    fill_val = f"[{parts_leaf(key)}]"
            deep_set(data, key, fill_val)
            filled[loc] += 1
            changed = True
        if changed or not (LOCALES / loc / f"{ns}.json").is_file():
            save_json(LOCALES / loc / f"{ns}.json", data)
            packs[loc] = data
    return filled


def parts_leaf(path: str) -> str:
    return path.split(".")[-1] if path else "value"


def check_terminology(terms: list[str]) -> list[str]:
    """Ensure product terms appear unchanged in DE catalog samples (smoke)."""
    issues: list[str] = []
    if not terms:
        issues.append("terminology.json has no terms")
        return issues
    # Smoke: DE client/vector must keep Website / Vector / Analytics as terms
    samples = [
        LOCALES / "de" / "client.json",
        LOCALES / "de" / "vector.json",
        LOCALES / "de" / "order.json",
    ]
    blob = "\n".join(p.read_text(encoding="utf-8") for p in samples if p.is_file())
    for term in ("Virtus Core", "Vector", "Website", "Analytics", "AI Assistant"):
        if term not in terms:
            issues.append(f"terminology missing required term: {term}")
        elif term not in blob:
            # soft — some catalogs may omit Virtus Core in seed
            if term in ("Vector", "Website", "Analytics", "AI Assistant"):
                if term not in blob:
                    issues.append(f"etalon DE catalogs missing term: {term}")
    return issues


def print_report(analyses: list[dict[str, Any]], legacy: list[dict[str, Any]]) -> None:
    print("=== L1 Locale Coverage Gate (etalon DE/EN/RU/UK) ===\n")
    for analysis in analyses:
        ns = analysis["namespace"]
        print(f"[{ns}] baseline_keys={analysis.get('baseline_keys', 0)}")
        if analysis.get("error"):
            print(f"  ERROR: {analysis['error']}")
            continue
        for loc in ETALON:
            info = analysis["locales"][loc]
            flag = "PASS" if info["ok"] else "FAIL"
            print(
                f"  {loc}: {info['coverage_pct']}%  keys={info['keys']}  "
                f"missing={len(info['missing'])} empty={len(info['empty'])} "
                f"extra={len(info['extra'])}  [{flag}]"
            )
            if info["missing"][:8]:
                print(f"    missing sample: {', '.join(info['missing'][:8])}")
            if info["empty"][:5]:
                print(f"    empty sample: {', '.join(info['empty'][:5])}")
        print()
    if legacy:
        print("[legacy chat — report only]")
        for analysis in legacy:
            for loc in ETALON:
                info = analysis["locales"].get(loc) or {}
                print(
                    f"  {loc}: {info.get('coverage_pct', 0)}% "
                    f"missing={len(info.get('missing') or [])}"
                )
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fill",
        action="store_true",
        help="Fill missing/empty keys from EN then DE (structure parity)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    if not LOCALES.is_dir():
        print(f"LOCALES missing: {LOCALES}", file=sys.stderr)
        return 2

    if args.fill:
        print("Filling missing keys for etalon namespaces…")
        for ns in REQUIRED_NS:
            counts = fill_ns(ns)
            print(f"  {ns}: {counts}")
        print()

    analyses = [analyze_ns(ns) for ns in REQUIRED_NS]
    legacy = [analyze_ns(ns) for ns in LEGACY_NS]
    term_issues = check_terminology(load_terminology())

    all_ok = all(a.get("ok") for a in analyses) and not term_issues

    if args.json:
        payload = {
            "ok": all_ok,
            "etalon": list(ETALON),
            "required": list(REQUIRED_NS),
            "namespaces": analyses,
            "legacy": legacy,
            "terminology_issues": term_issues,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_report(analyses, legacy)
        if term_issues:
            print("Terminology issues:")
            for issue in term_issues:
                print(f"  - {issue}")
            print()
        print("Summary:")
        for analysis in analyses:
            ns = analysis["namespace"]
            line_bits = []
            for loc in ETALON:
                info = analysis["locales"][loc]
                mark = "OK" if info["ok"] else "FAIL"
                line_bits.append(f"{loc}:{info['coverage_pct']}%[{mark}]")
            print(f"  {ns}: " + " ".join(line_bits))
        print()
        print("GATE:", "PASS" if all_ok else "FAIL")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
