#!/usr/bin/env python3
"""Check local Markdown navigation and docs/OpenSpec coverage, without writes."""

import argparse
import re
from pathlib import Path
from typing import Iterator, List, Optional, Set, Tuple
from urllib.parse import unquote, urlsplit


INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE = re.compile(r"^\s{0,3}\[(?!\^)[^\]\n]+\]:\s*(.+)$")
DESTINATION = re.compile(r"^(?:<([^>]+)>|(\S+))")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
CHANGE_DOCUMENTS = ("proposal.md", "spec.md", "design.md", "tasks.md", "work.md")


def markdown_links(content: str) -> Iterator[Tuple[int, str]]:
    """Read ordinary inline links and reference definitions outside fences."""
    marker = ""
    length = 0
    for number, line in enumerate(content.splitlines(), 1):
        fence = FENCE.match(line)
        if fence:
            run, suffix = fence.groups()
            if not marker:
                marker, length = run[0], len(run)
            elif run[0] == marker and len(run) >= length and not suffix.strip():
                marker, length = "", 0
            continue
        if marker:
            continue
        # Inline code is example text rather than a navigation link.
        line = re.sub(r"(`+).*?\1", "", line)
        reference = REFERENCE.match(line)
        values = [reference.group(1)] if reference else []
        values.extend(match.group(1) for match in INLINE_LINK.finditer(line))
        for value in values:
            destination = DESTINATION.match(value.strip())
            if destination:
                yield number, destination.group(1) or destination.group(2)


def local_target(source: Path, destination: str) -> Optional[Path]:
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def check(root: Path) -> Tuple[List[str], int, int]:
    root = root.resolve()
    errors = []  # type: List[str]
    docs = root / "docs"
    openspec = root / "openspec"
    required = [root / "AGENTS.md", root / "README.md", docs / "index.md", openspec / "index.md"]
    for path in required:
        if not path.is_file():
            errors.append("Missing entrypoint: {}".format(path.relative_to(root)))

    documents = sorted(docs.rglob("*.md")) if docs.is_dir() else []
    change_documents = sorted(openspec.rglob("*.md")) if openspec.is_dir() else []
    sources = set(documents)
    sources.update(change_documents)
    sources.update(path for path in required if path.is_file())
    skills = root / ".agents" / "skills"
    if skills.is_dir():
        sources.update(skills.rglob("*.md"))

    targets = {}  # type: dict[Path, Set[Path]]
    link_count = 0
    for source in sorted(sources):
        label = source.relative_to(root)
        targets[source] = set()
        for number, destination in markdown_links(source.read_text(encoding="utf-8")):
            try:
                target = local_target(source, destination)
            except ValueError as error:
                errors.append("{}:{}: Invalid link {} ({})".format(label, number, destination, error))
                continue
            if target is None:
                continue
            link_count += 1
            try:
                target.relative_to(root)
            except ValueError:
                errors.append("{}:{}: Link leaves repository: {}".format(label, number, destination))
                continue
            if Path(unquote(urlsplit(destination).path)).is_absolute():
                errors.append("{}:{}: Use a relative link: {}".format(label, number, destination))
                continue
            targets[source].add(target)
            if not target.exists():
                errors.append("{}:{}: Missing link target: {}".format(label, number, destination))

    for document in documents:
        if document == docs / "index.md":
            continue
        # Documents belong in their own directory index; indexes in their parent.
        index = (document.parent.parent if document.name == "index.md" else document.parent) / "index.md"
        if not index.is_file():
            errors.append("{}: Missing index {}".format(document.relative_to(root), index.relative_to(root)))
        elif document.resolve() not in targets.get(index, set()):
            errors.append("{}: Not linked from {}".format(document.relative_to(root), index.relative_to(root)))

    index = openspec / "index.md"
    if index.is_file() and index.resolve() not in targets.get(docs / "index.md", set()):
        errors.append("openspec/index.md: Not linked from docs/index.md")
    for document in change_documents:
        if document == index:
            continue
        if document.resolve() not in targets.get(index, set()):
            errors.append("{}: Not linked from openspec/index.md".format(document.relative_to(root)))

    changes = openspec / "changes"
    if changes.is_dir():
        for change in sorted(changes.iterdir()):
            if not change.is_dir() or change.name.startswith("."):
                continue
            for name in CHANGE_DOCUMENTS:
                document = change / name
                if not document.is_file():
                    errors.append("Missing change document: {}".format(document.relative_to(root)))

    return errors, len(documents) + len(change_documents), link_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[4],
        help="Repository root (defaults to the repository containing this script).",
    )
    arguments = parser.parse_args()
    errors, document_count, link_count = check(arguments.root)
    if errors:
        for error in errors:
            print("ERROR: " + error)
        print("FAIL: {} navigation error(s).".format(len(errors)))
        return 1
    print("PASS: {} docs/OpenSpec documents and {} local links; indexes and change files are connected.".format(document_count, link_count))
    print("Scope: local paths, index coverage, and required change files; excludes external URLs, heading anchors, and semantic consistency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
