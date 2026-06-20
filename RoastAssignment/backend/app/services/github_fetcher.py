"""Fetch a GitHub repository's text file contents for evaluation.

Repo metadata + the file tree are read via PyGithub (blocking, run in a thread
executor). Individual file contents are then fetched concurrently straight
from raw.githubusercontent.com via httpx, since PyGithub's `get_contents`
issues one blocking API call per file — sequentially, that's too slow to fit
in `settings.GITHUB_FETCH_TIMEOUT_SECONDS` for any repo with more than a
handful of files. The whole operation (tree read + concurrent file fetch) is
wrapped in that same overall timeout.
"""
import asyncio
import logging
import re

import httpx
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
_MAX_CONCURRENT_FILE_FETCHES = 10

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


def _blocking_list_files(github_repo_url: str) -> tuple[str, str, str, list[dict]]:
    """Blocking PyGithub work: resolve the repo and its size-bounded file list.

    Run inside a thread executor by `fetch_repo_files`. Returns
    (owner, repo_name, default_branch, entries) where each entry is
    {"path": str, "size": int} — content is fetched separately, concurrently.
    """
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

    entries: list[dict] = []
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
        if len(entries) >= settings.GITHUB_MAX_FILES:
            break
        if total_bytes + size > settings.GITHUB_MAX_TOTAL_BYTES:
            continue

        entries.append({"path": entry.path, "size": size})
        total_bytes += size

    return owner, repo_name, repo.default_branch, entries


async def _fetch_one_file(
    http_client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    owner: str,
    repo_name: str,
    branch: str,
    entry: dict,
) -> dict | None:
    """Fetch one file's raw content; returns None (and logs) on any failure."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{entry['path']}"
    async with semaphore:
        try:
            response = await http_client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Skipping %s: %s", entry["path"], exc)
            return None

    try:
        content = response.content.decode("utf-8", errors="replace")
    except Exception as exc:  # defensive: never let a single file kill the whole fetch
        logger.warning("Could not decode %s: %s", entry["path"], exc)
        return None

    return {"path": entry["path"], "content": content, "size": entry["size"]}


async def fetch_repo_files(github_repo_url: str) -> list[dict]:
    """Fetch a representative, size-bounded set of text files from a GitHub repo.

    Returns a list of {"path": str, "content": str, "size": int}.
    Raises GitHubFetchError on invalid URL, missing/private repo, rate limiting,
    timeout, or if limits are hit with zero usable files.
    """
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            _fetch_repo_files_inner(loop, github_repo_url),
            timeout=settings.GITHUB_FETCH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise GitHubFetchError(
            f"Timed out fetching repo files after {settings.GITHUB_FETCH_TIMEOUT_SECONDS}s."
        ) from exc


async def _fetch_repo_files_inner(
    loop: asyncio.AbstractEventLoop, github_repo_url: str
) -> list[dict]:
    owner, repo_name, branch, entries = await loop.run_in_executor(
        None, _blocking_list_files, github_repo_url
    )

    if not entries:
        raise GitHubFetchError(
            f"No usable files found in '{owner}/{repo_name}' "
            "(repo empty, or all files excluded by size/extension limits)."
        )

    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"} if settings.GITHUB_TOKEN else {}
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_FILE_FETCHES)

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as http_client:
        results = await asyncio.gather(
            *(
                _fetch_one_file(http_client, semaphore, owner, repo_name, branch, entry)
                for entry in entries
            )
        )

    files = [f for f in results if f is not None]
    if not files:
        raise GitHubFetchError(
            f"No usable files found in '{owner}/{repo_name}' "
            "(repo empty, or all files excluded by size/extension limits)."
        )

    return files
