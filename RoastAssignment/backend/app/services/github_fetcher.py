"""Fetch a GitHub repository's text file contents for evaluation.

Uses PyGithub. Network calls are blocking, so they are run in a thread executor
and wrapped with an overall timeout (`settings.GITHUB_FETCH_TIMEOUT_SECONDS`).
"""
import asyncio
import logging
import re

from github import Github
from github.GithubException import GithubException, RateLimitExceededException

from app.config import settings

logger = logging.getLogger(__name__)

# Extensions we never want to send to the AI / static analyzer.
_BINARY_OR_HUGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".jar", ".war",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".class",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".lock", ".min.js", ".min.css",
    ".pyc", ".pyo",
}

_MAX_PER_FILE_BYTES = 100_000

_GITHUB_URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
)


class GitHubFetchError(Exception):
    """Raised whenever a repo's files can't be fetched (bad URL, 404/private, rate limit, timeout)."""


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a github.com URL.

    Raises GitHubFetchError if `url` is not a recognizable github.com repo URL.
    """
    if not url or not isinstance(url, str):
        raise GitHubFetchError(f"Invalid GitHub URL: {url!r}")

    match = _GITHUB_URL_RE.match(url.strip())
    if not match:
        raise GitHubFetchError(f"Invalid GitHub URL format: {url!r}")

    owner, repo = match.group(1), match.group(2)
    if not owner or not repo:
        raise GitHubFetchError(f"Invalid GitHub URL format: {url!r}")
    return owner, repo


def _is_excluded(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(ext) for ext in _BINARY_OR_HUGE_EXTENSIONS)


def _blocking_fetch(github_repo_url: str) -> list[dict]:
    """Blocking PyGithub work; run inside a thread executor by `fetch_repo_files`."""
    owner, repo_name = parse_github_url(github_repo_url)

    client = Github(settings.GITHUB_TOKEN or None)

    try:
        repo = client.get_repo(f"{owner}/{repo_name}")
    except RateLimitExceededException as exc:
        raise GitHubFetchError("GitHub API rate limit exceeded.") from exc
    except GithubException as exc:
        if exc.status == 404:
            raise GitHubFetchError(
                f"Repository '{owner}/{repo_name}' not found or private."
            ) from exc
        raise GitHubFetchError(f"GitHub API error: {exc.data}") from exc

    try:
        tree = repo.get_git_tree(repo.default_branch, recursive=True)
    except RateLimitExceededException as exc:
        raise GitHubFetchError("GitHub API rate limit exceeded.") from exc
    except GithubException as exc:
        raise GitHubFetchError(f"Failed to read repo tree: {exc.data}") from exc

    files: list[dict] = []
    total_bytes = 0

    for entry in tree.tree:
        if entry.type != "blob":
            continue
        if _is_excluded(entry.path):
            continue
        # `entry.size` is the blob size in bytes (may be None for some entries).
        size = entry.size or 0
        if size > _MAX_PER_FILE_BYTES:
            continue
        if len(files) >= settings.GITHUB_MAX_FILES:
            break
        if total_bytes + size > settings.GITHUB_MAX_TOTAL_BYTES:
            continue

        try:
            content_file = repo.get_contents(entry.path)
        except RateLimitExceededException as exc:
            raise GitHubFetchError("GitHub API rate limit exceeded.") from exc
        except GithubException as exc:
            logger.warning("Skipping %s: %s", entry.path, exc.data)
            continue

        # `get_contents` can return a list if `path` is a directory; skip those.
        if isinstance(content_file, list):
            continue

        try:
            decoded = content_file.decoded_content.decode("utf-8", errors="replace")
        except Exception as exc:  # defensive: never let a single file kill the whole fetch
            logger.warning("Could not decode %s: %s", entry.path, exc)
            continue

        files.append({"path": entry.path, "content": decoded, "size": size})
        total_bytes += size

    if not files:
        raise GitHubFetchError(
            f"No usable files found in '{owner}/{repo_name}' "
            "(repo empty, or all files excluded by size/extension limits)."
        )

    return files


async def fetch_repo_files(github_repo_url: str) -> list[dict]:
    """Fetch a representative, size-bounded set of text files from a GitHub repo.

    Returns a list of {"path": str, "content": str, "size": int}.
    Raises GitHubFetchError on invalid URL, missing/private repo, rate limiting,
    timeout, or if limits are hit with zero usable files.
    """
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _blocking_fetch, github_repo_url),
            timeout=settings.GITHUB_FETCH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise GitHubFetchError(
            f"Timed out fetching repo files after {settings.GITHUB_FETCH_TIMEOUT_SECONDS}s."
        ) from exc
