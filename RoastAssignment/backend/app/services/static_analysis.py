"""Lightweight, dependency-free static analysis heuristics.

NOTE: This is a stand-in for real linters (ruff for Python, eslint for JS/TS).
We can't assume `pip install`/`npm install` has been run for those tools in
every environment this code executes in, so this module implements simple,
language-aware heuristics using only the stdlib. Once ruff/eslint are
confirmed available as subprocesses, this module's heuristics can be replaced
(or supplemented) with real linter output while keeping the same
`(report_dict, score)` return contract.
"""
import os
from collections import Counter

_LONG_FILE_LINE_THRESHOLD = 500

_LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell",
}

# Penalty weights, applied per flagged issue and floored at 0.0 overall.
_PENALTY_NO_DOCSTRING_OR_COMMENTS = 0.02
_PENALTY_LONG_FILE = 0.03
_PENALTY_DUPLICATE_FILENAME = 0.02


def _extension(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _language_for(path: str) -> str:
    return _LANGUAGE_BY_EXTENSION.get(_extension(path), "Other")


def _has_no_docstring_or_comments(content: str) -> bool:
    """Very crude heuristic: no '#' comment lines and no triple-quoted docstring."""
    if not content.strip():
        return False  # empty files aren't flagged for lacking docs
    has_comment = any(line.strip().startswith("#") for line in content.splitlines())
    has_docstring = '"""' in content or "'''" in content
    return not has_comment and not has_docstring


def run_static_analysis(files: list[dict]) -> tuple[dict, float]:
    """Run lightweight heuristic checks across `files`.

    Returns (report_dict, score) where score is a 0.0-1.0 heuristic starting at 1.0
    with small penalties subtracted per flagged issue, floored at 0.0.
    """
    score = 1.0
    issues: list[dict] = []

    total_files = len(files)
    total_loc = 0
    language_counts: Counter = Counter()
    long_files: list[str] = []
    files_missing_docs_or_comments: list[str] = []

    basenames = [os.path.basename(f["path"]) for f in files]
    basename_counts = Counter(basenames)
    duplicate_basenames = {name for name, count in basename_counts.items() if count > 1}
    flagged_duplicate_paths: list[str] = []

    for f in files:
        path = f["path"]
        content = f.get("content", "")
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        total_loc += line_count

        language = _language_for(path)
        language_counts[language] += 1

        if line_count > _LONG_FILE_LINE_THRESHOLD:
            long_files.append(path)
            issues.append({"type": "long_file", "path": path, "lines": line_count})
            score -= _PENALTY_LONG_FILE

        if _extension(path) == ".py" and _has_no_docstring_or_comments(content):
            files_missing_docs_or_comments.append(path)
            issues.append({"type": "no_docstring_or_comments", "path": path})
            score -= _PENALTY_NO_DOCSTRING_OR_COMMENTS

        basename = os.path.basename(path)
        if basename in duplicate_basenames:
            flagged_duplicate_paths.append(path)
            issues.append({"type": "duplicate_filename", "path": path, "filename": basename})
            score -= _PENALTY_DUPLICATE_FILENAME

    score = max(0.0, min(1.0, score))

    report = {
        "total_files": total_files,
        "total_loc": total_loc,
        "language_breakdown": dict(language_counts),
        "long_files": long_files,
        "files_missing_docs_or_comments": files_missing_docs_or_comments,
        "duplicate_filenames": sorted(duplicate_basenames),
        "issues": issues,
        "issue_count": len(issues),
        "note": (
            "Lightweight heuristic static analysis (no external linters run). "
            "Swap in ruff/eslint subprocess calls once those deps are confirmed installed."
        ),
    }

    return report, score
