#!/usr/bin/env python3
"""Validate decision records under docs/decisions/.

Enforces the rules in docs/decisions/README.md: frontmatter shape, unique
ids matching filenames, legal status transitions, reciprocal supersession
links, and body immutability once a record is accepted, rejected or
superseded.

Dependency-free stdlib Python. Parses a deliberately small YAML subset —
scalars, quoted strings, inline lists, null. Anything outside that is
rejected rather than guessed at.

Usage:
    python3 scripts/validate-decisions.py                 # static checks only
    python3 scripts/validate-decisions.py --base main     # plus diff checks
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"

LIFECYCLE_STATUSES = {"draft", "in-review", "accepted", "rejected", "superseded"}
LOCKED_STATUSES = {"accepted", "rejected", "superseded"}
LEGAL_TRANSITIONS = {
    "draft": {"in-review", "rejected"},
    "in-review": {"draft", "accepted", "rejected"},
    "accepted": {"superseded"},
    "rejected": set(),
    "superseded": set(),
}
REQUIRED_KEYS = [
    "id", "title", "status", "date", "deciders",
    "supersedes", "superseded-by", "affects", "design-doc",
]
MUTABLE_KEYS = {"status", "superseded-by"}
FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9-]+)\.md$")


# ---- the small YAML-subset parser ----

def strip_comment(line):
    in_quotes = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == "#" and not in_quotes:
            return line[:i]
    return line


def unquote(s):
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def parse_value(raw):
    val = raw.strip()
    if val in ("", "null"):
        return None
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [unquote(item.strip()) for item in inner.split(",")]
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    return unquote(val)


def parse_record(text):
    """Returns (frontmatter dict, body str, list of parse errors)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text, ["file must start with a '---' frontmatter delimiter"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text, ["frontmatter has no closing '---'"]

    data = {}
    errors = []
    for raw in lines[1:end]:
        line = strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"unparseable frontmatter line: {raw!r}")
            continue
        key, _, val = line.partition(":")
        data[key.strip()] = parse_value(val)

    body = "\n".join(lines[end + 1:]).strip("\n")
    return data, body, errors


def load_records(directory):
    """Returns {path: (frontmatter, body, parse_errors)} for every real record.

    Only files matching <4-digit-id>-<slug>.md are records. Everything else
    in the directory — README.md, _template.md, anything underscore-prefixed
    — documents or scaffolds the process rather than being part of the log.
    """
    records = {}
    if not directory.is_dir():
        return records
    for path in sorted(directory.glob("*.md")):
        if FILENAME_RE.match(path.name):
            records[path] = parse_record(path.read_text(encoding="utf-8"))
    return records


# ---- static checks ----

def static_checks(records):
    errors = []
    by_id = {}

    for path, (fm, body, parse_errors) in records.items():
        prefix = f"{path.relative_to(REPO_ROOT)}: "
        errors += [prefix + e for e in parse_errors]
        if parse_errors:
            continue

        for key in REQUIRED_KEYS:
            if key not in fm:
                errors.append(prefix + f"missing required key '{key}'")

        m = FILENAME_RE.match(path.name)
        if not m:
            errors.append(prefix + "filename must match <4-digit-id>-<slug>.md")
            continue
        filename_id = int(m.group(1))

        fm_id = fm.get("id")
        if not isinstance(fm_id, int):
            errors.append(prefix + "frontmatter 'id' must be an integer")
        elif fm_id != filename_id:
            errors.append(prefix + f"frontmatter id {fm_id} does not match filename id {filename_id}")
        elif fm_id in by_id:
            errors.append(prefix + f"id {fm_id} is also used by {by_id[fm_id][0].name}")
        else:
            by_id[fm_id] = (path, fm)

        title = fm.get("title")
        if not title or not isinstance(title, str):
            errors.append(prefix + "'title' must be a non-empty string")

        status = fm.get("status")
        if status not in LIFECYCLE_STATUSES:
            errors.append(prefix + f"'status' must be one of {sorted(LIFECYCLE_STATUSES)}, got {status!r}")

        raw_date = fm.get("date")
        if not isinstance(raw_date, str):
            errors.append(prefix + "'date' must be an ISO-8601 string")
        else:
            try:
                date.fromisoformat(raw_date)
            except ValueError:
                errors.append(prefix + f"'date' is not valid ISO-8601: {raw_date!r}")

        for list_key in ("deciders", "affects"):
            val = fm.get(list_key)
            if not isinstance(val, list) or not val or not all(isinstance(x, str) and x for x in val):
                errors.append(prefix + f"'{list_key}' must be a non-empty list of non-empty strings")

    # supersession reciprocity, now that every id is known
    for fm_id, (path, fm) in by_id.items():
        prefix = f"{path.relative_to(REPO_ROOT)}: "
        supersedes = fm.get("supersedes")
        superseded_by = fm.get("superseded-by")

        if supersedes is not None:
            parent = by_id.get(supersedes)
            if parent is None:
                errors.append(prefix + f"supersedes {supersedes}, which does not exist")
            else:
                parent_path, parent_fm = parent
                if parent_fm.get("superseded-by") != fm_id:
                    errors.append(prefix + f"supersedes {supersedes}, but {parent_path.name} does not point back via superseded-by")
                if parent_fm.get("status") != "superseded":
                    errors.append(prefix + f"supersedes {supersedes}, but {parent_path.name} is not status 'superseded'")

        if superseded_by is not None:
            child = by_id.get(superseded_by)
            if child is None:
                errors.append(prefix + f"superseded-by {superseded_by}, which does not exist")
            elif child[1].get("supersedes") != fm_id:
                errors.append(prefix + f"superseded-by {superseded_by}, but {child[0].name} does not point back via supersedes")
            if fm.get("status") != "superseded":
                errors.append(prefix + "has 'superseded-by' set but status is not 'superseded'")

    return errors


# ---- diff checks (PRs only) ----

def git_show(rev, relpath):
    """Returns file text at rev:relpath, or None if it doesn't exist there."""
    result = subprocess.run(
        ["git", "show", f"{rev}:{relpath}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def git_diff_status(base):
    """Returns raw `git diff --name-status -M` output for the whole repo,
    following renames. Deliberately unscoped to docs/decisions/ — a record
    that moves directory (e.g. into or out of docs/decisions/) must still
    be paired with its old self, or a rename becomes a loophole around
    immutability. Results are filtered to record-shaped filenames by the
    caller instead.
    """
    commands = [
        ["git", "diff", "--name-status", "-M", f"{base}...HEAD"],
        ["git", "diff", "--name-status", "-M", base, "HEAD"],
    ]
    for cmd in commands:
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
    return ""


def parse_diff_status(output):
    """Yields (old_relpath_or_None, new_relpath_or_None) per changed path.

    Renames (a plain path move, e.g. decisions/ -> docs/decisions/) resolve
    to both sides so the old content can still be diffed against the new —
    a rename must never be a loophole around immutability.
    """
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")):
            yield parts[1], parts[2]
        elif status == "A":
            yield None, parts[1]
        elif status == "D":
            yield parts[1], None
        else:  # M, T, ...
            yield parts[1], parts[1]


def read_record(path, records):
    if path in records:
        return records[path]
    if path.exists():
        return parse_record(path.read_text(encoding="utf-8"))
    return None


def diff_checks(base, records):
    errors = []

    for old_rel, new_rel in parse_diff_status(git_diff_status(base)):
        relevant_name = Path(new_rel or old_rel).name
        if not FILENAME_RE.match(relevant_name):
            continue
        prefix = f"{new_rel or old_rel}: "

        if new_rel is None:
            continue  # deleted — not covered by the documented rules

        new_record = read_record(REPO_ROOT / new_rel, records)
        if new_record is None:
            continue
        new_fm, new_body, new_errs = new_record
        if new_errs:
            continue  # malformed — already reported by static checks

        if old_rel is None:
            if new_fm.get("status") == "superseded":
                errors.append(prefix + "a new record cannot be created with status 'superseded'")
            continue

        old_text = git_show(base, old_rel)
        if old_text is None:
            continue  # shouldn't happen if git reported this as a change, but don't crash the lint over it

        old_fm, old_body, old_errs = parse_record(old_text)
        if old_errs:
            continue

        old_status = old_fm.get("status")
        new_status = new_fm.get("status")

        if old_status in LOCKED_STATUSES:
            changed_fields = [
                k for k in REQUIRED_KEYS
                if k not in MUTABLE_KEYS and old_fm.get(k) != new_fm.get(k)
            ]
            if changed_fields or old_body.strip() != new_body.strip():
                what = ", ".join(changed_fields) if changed_fields else "body"
                errors.append(
                    prefix + f"record was '{old_status}' — only 'status' and 'superseded-by' "
                    f"may change once accepted, rejected or superseded (changed: {what})"
                )

        if new_status != old_status and new_status not in LEGAL_TRANSITIONS.get(old_status, set()):
            errors.append(prefix + f"illegal status transition '{old_status}' -> '{new_status}'")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate decision records under docs/decisions/.")
    parser.add_argument("--base", help="Base ref to diff against for lifecycle/immutability checks (e.g. origin/main).")
    args = parser.parse_args()

    records = load_records(DECISIONS_DIR)
    errors = static_checks(records)
    if args.base:
        errors += diff_checks(args.base, records)

    if errors:
        print(f"decision record validation failed ({len(errors)} issue{'s' if len(errors) != 1 else ''}):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    scope = "static + diff" if args.base else "static"
    print(f"decision records OK ({scope} checks, {len(records)} record{'s' if len(records) != 1 else ''}).")


if __name__ == "__main__":
    main()
