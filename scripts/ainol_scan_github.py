#!/usr/bin/env python3
"""AINOL GitHub issue scanner.

Reads issues from a public/private GitHub repo, compares them with a local state
file, and writes a report ONLY when there are material changes. It is safe for
cron/GitHub Actions: no changes => no output file and exit 0.

Secrets: token is read from GH_TOKEN/GITHUB_TOKEN, never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API = "https://api.github.com"


def api_get(path: str, token: str | None) -> Any:
    url = API + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "AINOL-issue-scanner/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining")
            reset = resp.headers.get("X-RateLimit-Reset")
            if remaining == "0":
                raise RuntimeError(f"GitHub rate limit exhausted; reset={reset}")
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub API {e.code} for {path}: {body}") from e


def fetch_issues(repo: str, token: str | None, since: str | None, max_pages: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    params = {"state": "all", "per_page": "100", "sort": "updated", "direction": "desc"}
    if since:
        params["since"] = since
    for page in range(1, max_pages + 1):
        q = urllib.parse.urlencode({**params, "page": str(page)})
        data = api_get(f"/repos/{repo}/issues?{q}", token)
        if not isinstance(data, list):
            raise RuntimeError("GitHub API returned non-list issue payload")
        # Pull requests appear in the issues API; ignore them for the需求池 scan.
        batch = [x for x in data if "pull_request" not in x]
        issues.extend(batch)
        if len(data) < 100:
            break
    return issues


def slim(issue: dict[str, Any]) -> dict[str, Any]:
    labels = sorted(l.get("name", "") for l in issue.get("labels", []) if l.get("name"))
    assignees = sorted(a.get("login", "") for a in issue.get("assignees", []) if a.get("login"))
    return {
        "number": issue["number"],
        "title": issue.get("title", ""),
        "state": issue.get("state", ""),
        "labels": labels,
        "assignees": assignees,
        "updated_at": issue.get("updated_at", ""),
        "closed_at": issue.get("closed_at"),
        "html_url": issue.get("html_url", ""),
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"issues": {}, "last_scan_at": None}
    return json.loads(path.read_text())


def classify_change(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any] | None:
    if old is None:
        return {"kind": "new_issue", "issue": new, "fields": ["created"]}
    changed = [k for k in ["title", "state", "labels", "assignees", "closed_at"] if old.get(k) != new.get(k)]
    if not changed:
        return None
    kind = "issue_updated"
    if "closed_at" in changed and new.get("closed_at"):
        kind = "issue_closed"
    if old.get("state") != new.get("state") and new.get("state") == "open":
        kind = "issue_reopened"
    if old.get("labels") != new.get("labels") and "status/changes-requested" in new.get("labels", []):
        kind = "review_changes_requested"
    if old.get("labels") != new.get("labels") and "status/prd-ready" in new.get("labels", []):
        kind = "prd_ready"
    return {"kind": kind, "issue": new, "previous": old, "fields": changed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/repo")
    ap.add_argument("--state", default=".ainol-state.json")
    ap.add_argument("--out", default="ainol-scan-report.json")
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("--quiet", action="store_true", help="suppress summary on stderr")
    args = ap.parse_args()

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    state_path = Path(args.state)
    out_path = Path(args.out)
    state = load_state(state_path)
    old_issues: dict[str, Any] = state.get("issues", {})
    since = state.get("last_scan_at")

    issues = fetch_issues(args.repo, token, since, args.max_pages)
    new_issues = {str(i["number"]): slim(i) for i in issues}
    merged_issues = {**old_issues, **new_issues}

    changes = []
    for num, new in sorted(new_issues.items(), key=lambda kv: int(kv[0])):
        ch = classify_change(old_issues.get(num), new)
        if ch:
            changes.append(ch)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state_path.write_text(json.dumps({"last_scan_at": now, "issues": merged_issues}, ensure_ascii=False, indent=2) + "\n")

    if changes:
        report = {"repo": args.repo, "scan_at": now, "changes": changes}
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if not args.quiet:
            print(f"AINOL scan: {len(changes)} change(s) -> {out_path}", file=sys.stderr)
    else:
        if out_path.exists():
            out_path.unlink()
        if not args.quiet:
            print("AINOL scan: no changes; no report written", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
