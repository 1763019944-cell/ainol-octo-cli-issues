#!/usr/bin/env python3
"""Reject implementation-heavy PRD text.

AINOL PRDs must describe What, not How. This guard is intentionally simple and
explainable; it flags suspicious implementation terms for human/agent review.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    (r"\bRedis\b|缓存", "不要指定缓存/Redis等实现方案"),
    (r"数据库|数据表|建表|字段名|schema", "不要指定数据库/内部字段设计"),
    (r"接口返回\s*200|HTTP\s*200|status\s*code", "验收标准应写用户可感知结果，不写接口状态码"),
    (r"```", "PRD 不应包含代码块"),
    (r"\bSQL\b|SELECT\b|INSERT\b|UPDATE\b", "不要在 PRD 中写 SQL/内部实现"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    text = Path(args.path).read_text(errors="ignore")
    hits = []
    for pat, reason in PATTERNS:
        for m in re.finditer(pat, text, flags=re.I):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((line, m.group(0), reason))
    if hits:
        print("PRD Guard failed: detected How/implementation details", file=sys.stderr)
        for line, token, reason in hits:
            print(f"- L{line}: {token!r} — {reason}", file=sys.stderr)
        return 2
    print("PRD Guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
