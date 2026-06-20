"""Generate a witty-but-constructive AI "roast" code review using Anthropic's API."""
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_PROMPT_CHARS = 50_000

_SCORE_LINE_RE = re.compile(r"^\s*SCORE:\s*(\d{1,3})\s*$", re.IGNORECASE | re.MULTILINE)

_SYSTEM_PROMPT = (
    "You are a senior software engineer doing a code review for a coding bootcamp "
    "assignment submission. Give a witty, entertaining, but ultimately constructive "
    "'roast' of the code: call out real problems (bugs, bad practices, missing error "
    "handling, poor structure, naming, etc.) with humor, but also point out what was "
    "done well and how to improve. Be specific and reference actual file paths/snippets "
    "from what's given to you. End your entire response with exactly one line in the "
    "exact format `SCORE: <integer>` where <integer> is your overall quality score "
    "from 0 to 100 (0 = unusable, 100 = excellent). Do not put anything after that line."
)


def _build_prompt(files: list[dict]) -> str:
    """Concatenate path+content from a representative sample of files, truncated to a safe length.

    Prioritizes larger files first (a rough proxy for "more central" to the project),
    then fills in remaining budget with the rest in original order.
    """
    if not files:
        return "No files were available to review."

    sorted_by_size = sorted(files, key=lambda f: f.get("size", len(f.get("content", ""))), reverse=True)

    parts: list[str] = []
    total_len = 0
    included_paths: set[str] = set()

    for f in sorted_by_size:
        path = f["path"]
        content = f.get("content", "")
        chunk = f"\n\n--- FILE: {path} ---\n{content}"
        if total_len + len(chunk) > _MAX_PROMPT_CHARS:
            remaining = _MAX_PROMPT_CHARS - total_len
            if remaining > 200:  # only bother with a meaningful truncated chunk
                parts.append(chunk[:remaining] + "\n... [truncated]")
                total_len += remaining
            break
        parts.append(chunk)
        total_len += len(chunk)
        included_paths.add(path)

    return "Here are the files from the submitted repository:" + "".join(parts)


def _parse_score(text: str) -> tuple[str, float]:
    """Pull the trailing `SCORE: <0-100>` line out of `text`.

    Returns (text_without_score_line, score_as_0_to_1_float). Defaults to 0.0 if no
    score line is found.
    """
    match = _SCORE_LINE_RE.search(text)
    if not match:
        logger.warning("AI roast response had no parseable SCORE line.")
        return text.strip(), 0.0

    raw_score = int(match.group(1))
    raw_score = max(0, min(100, raw_score))
    cleaned_text = _SCORE_LINE_RE.sub("", text).strip()
    return cleaned_text, raw_score / 100.0


async def generate_roast(files: list[dict]) -> tuple[str, float]:
    """Generate an AI roast + normalized score (0.0-1.0) for the given files.

    Never raises: on missing API key, API errors, or unparseable responses, returns a
    fallback message and a score of 0.0 so the evaluation pipeline can keep going.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not configured; skipping AI roast.")
        return "AI roast skipped: ANTHROPIC_API_KEY not configured.", 0.0

    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed; skipping AI roast.")
        return "AI roast skipped: anthropic package not installed.", 0.0

    prompt = _build_prompt(files)

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        if not text.strip():
            raise ValueError("Empty response from Anthropic API")
        return _parse_score(text)
    except Exception as exc:  # noqa: BLE001 - must never break the evaluation pipeline
        logger.error("AI roast generation failed: %s", exc, exc_info=True)
        return f"AI roast failed: {exc}", 0.0
