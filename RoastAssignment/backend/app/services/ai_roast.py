"""Generate a witty-but-constructive AI "roast" code review using OpenAI's API."""
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_PROMPT_CHARS = 50_000

_SCORE_LINE_RE = re.compile(r"^\s*SCORE:\s*(\d{1,3})\s*$", re.IGNORECASE | re.MULTILINE)

_SYSTEM_PROMPT = (
    "You are a senior software engineer doing a code review for a coding bootcamp "
    "assignment submission. Be specific and reference actual file paths/snippets from "
    "what's given to you. Structure your ENTIRE response as exactly these three "
    "markdown sections, in this order, each starting with a `## ` heading line:\n\n"
    "## The Good Stuff\n"
    "What was done well — be genuinely specific, not generic praise.\n\n"
    "## The Roast\n"
    "This is the fun part — really lean into the comedy here. Be genuinely funny: use "
    "vivid analogies, exaggeration, and a sarcastic, stand-up-comedian tone while roasting "
    "the code's real problems (bugs, bad practices, missing error handling, poor "
    "structure, naming, etc.). Don't be mean-spirited, but don't hold back the jokes "
    "either — this should make the reader laugh out loud, not just smile politely.\n\n"
    "## Overall Verdict\n"
    "A short closing summary of where this submission stands and the top 1-3 things "
    "to fix next.\n\n"
    "After those three sections, end your entire response with exactly one line in "
    "the exact format `SCORE: <integer>` where <integer> is your overall quality score "
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
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured; skipping AI roast.")
        return "AI roast skipped: OPENAI_API_KEY not configured.", 0.0

    try:
        import openai
    except ImportError:
        logger.error("openai package not installed; skipping AI roast.")
        return "AI roast skipped: openai package not installed.", 0.0

    prompt = _build_prompt(files)

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        if not text.strip():
            raise ValueError("Empty response from OpenAI API")
        return _parse_score(text)
    except Exception as exc:  # noqa: BLE001 - must never break the evaluation pipeline
        logger.error("AI roast generation failed: %s", exc, exc_info=True)
        return f"AI roast failed: {exc}", 0.0
