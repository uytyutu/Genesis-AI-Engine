#!/usr/bin/env python3
"""CEO product verification helper — PDF Intake (mechanical checks only).

Does NOT replace human verification on /site (Genesis.exe → /site).
Use this to pre-flight PDF text extraction before asking Vector questions.

Usage (from repo root):
  py scripts/pdf_intake_ceo_verify.py path/to/document.pdf
  py scripts/pdf_intake_ceo_verify.py path/to/folder/*.pdf
  py scripts/pdf_intake_ceo_verify.py brief.pdf --questions

Paraphrase reasoning test (manual on /site):
  1) «Когда нужно поставить товар?»
  2) «Какие сроки указаны для выполнения обязательств?»
  3) «Есть ли дедлайн?»
  → same PDF, no re-upload — all three should reference the same fact.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BACKEND = _REPO / "dashboard" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.integration.attachment_policy import AttachmentPolicy  # noqa: E402
from app.integration.knowledge_intake_pdf import extract_pdf_text  # noqa: E402


def _check_pdf(path: Path, *, max_pages: int) -> dict:
    try:
        text, total, included = extract_pdf_text(path, max_pages=max_pages)
    except Exception as exc:
        return {"file": path.name, "ok": False, "error": str(exc)}
    preview = text[:600].replace("\n", " ")
    return {
        "file": path.name,
        "ok": bool(text.strip()),
        "pages_total": total,
        "pages_included": included,
        "chars": len(text),
        "preview": preview + ("…" if len(text) > 600 else ""),
        "warning": None
        if text.strip()
        else "NO EXTRACTABLE TEXT — likely scan/image PDF; Vector cannot read this yet.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF Intake CEO verify — extraction pre-flight")
    parser.add_argument("paths", nargs="+", help="PDF file(s) or directories")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Pages to extract (default: free tier cap)",
    )
    parser.add_argument(
        "--questions",
        action="store_true",
        help="Print suggested CEO questions for /site",
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.pdf")))
        elif path.suffix.lower() == ".pdf":
            files.append(path)

    if not files:
        print("No PDF files found.", file=sys.stderr)
        return 1

    policy = AttachmentPolicy()
    limits = policy.limits_for("free")
    print("=== PDF Intake — CEO pre-flight (extraction only) ===")
    print(f"Free tier: {limits.max_parsed_documents_per_day} doc/day, {limits.max_parsed_pages_per_day} pages/doc")
    print()

    results = []
    for f in files:
        row = _check_pdf(f, max_pages=min(args.max_pages, limits.max_parsed_pages_per_day))
        results.append(row)
        status = "OK" if row.get("ok") else "FAIL"
        print(f"[{status}] {row['file']}")
        if row.get("error"):
            print(f"  error: {row['error']}")
        else:
            print(f"  pages: {row.get('pages_included')}/{row.get('pages_total')}  chars: {row.get('chars')}")
            if row.get("warning"):
                print(f"  ⚠ {row['warning']}")
            else:
                print(f"  preview: {row.get('preview')}")
        print()

    if args.questions:
        print("--- Suggested /site questions (per document) ---")
        for row in results:
            if not row.get("ok"):
                continue
            name = row["file"]
            print(f"\n{name}:")
            print("  1. О чём этот документ? (кратко)")
            print("  2. Найди конкретный факт: срок / цена / пункт.")
            print("  3. Спроси то, чего в PDF нет → ожидай «не нашёл в документе».")
            print("  4. Без повторной загрузки — перефразируй тот же вопрос 2–3 раза.")

    print("--- Paraphrase test (manual) ---")
    print("Same PDF, no re-upload:")
    print('  • «Когда нужно поставить товар?»')
    print('  • «Какие сроки указаны для выполнения обязательств?»')
    print('  • «Есть ли дедлайн?»')
    print("→ все три должны ссылаться на один факт из PDF.")

    ok_count = sum(1 for r in results if r.get("ok"))
    print()
    print(f"Extraction OK: {ok_count}/{len(results)}")
    print("Reasoning + honesty: verify on Genesis.exe → /site only.")
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if ok_count == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
