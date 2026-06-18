import re

VALID_TOKENS = {"YYYY", "YY", "MM", "M", "DD", "D", "HH", "H", "mm", "m", "ss", "s"}
VALID_SEPARATORS = {"-", "/", ".", " ", ":", ",", "T"}

# Regex that matches all tokens, longest first so YYYY beats YY, MM beats M, etc.
TOKEN_RE = re.compile(r"(YYYY|YY|MM|M|DD|D|HH|H|mm|m|ss|s)")


def validate_datetime_format(format_str: str) -> tuple[bool, str]:
    """Validate a datetime format pattern string.

    Valid tokens: YYYY, YY, MM, M, DD, D, HH, H, mm, m, ss, s
    Valid separators: -, /, ., space, :, ,, T

    Returns (is_valid, error_message). If valid, error_message is empty.
    """
    if not format_str or not format_str.strip():
        return False, "Format pattern cannot be empty"

    format_str = format_str.strip()

    # Tokenize: split the pattern into tokens and separators
    parts = TOKEN_RE.split(format_str)

    found_tokens = []
    separators_or_literals = []

    for i, part in enumerate(parts):
        if i % 2 == 0:
            separators_or_literals.append(part)
        else:
            found_tokens.append(part)

    if not found_tokens:
        return (
            False,
            "Format pattern must contain at least one date/time token (e.g., YYYY, MM, DD, HH, mm, ss)",
        )

    # Check for unknown tokens: any letter sequence that's not a valid token
    all_letter_seqs = re.findall(r"[A-Za-z]+", format_str)
    for seq in all_letter_seqs:
        if seq not in VALID_TOKENS:
            return (
                False,
                f"Unknown format token '{seq}'. Valid tokens: YYYY, YY, MM, M, DD, D, HH, H, mm, m, ss, s",
            )

    # Must contain a year token
    has_year = "YYYY" in found_tokens or "YY" in found_tokens
    has_month = "MM" in found_tokens or "M" in found_tokens
    has_day = "DD" in found_tokens or "D" in found_tokens

    if not has_year:
        return False, "Format pattern must include a year token (YYYY or YY)"

    if not has_month and not has_day:
        return (
            False,
            "Format pattern must include at least a month (MM/M) or day (DD/D) token",
        )

    return True, ""


def format_datetime(dt, pattern: str) -> str:
    """Format a datetime object using the custom pattern.

    Uses a single-pass regex replacement to avoid token collision issues
    where short tokens (M, D, etc.) would match inside replacement values
    of longer tokens.
    """

    def _replace(match: re.Match) -> str:
        token = match.group(1)
        if token == "YYYY":
            return f"{dt.year:04d}"
        if token == "YY":
            return f"{dt.year % 100:02d}"
        if token == "MM":
            return f"{dt.month:02d}"
        if token == "M":
            return str(dt.month)
        if token == "DD":
            return f"{dt.day:02d}"
        if token == "D":
            return str(dt.day)
        if token == "HH":
            return f"{dt.hour:02d}"
        if token == "H":
            return str(dt.hour)
        if token == "mm":
            return f"{dt.minute:02d}"
        if token == "m":
            return str(dt.minute)
        if token == "ss":
            return f"{dt.second:02d}"
        if token == "s":
            return str(dt.second)
        return match.group(0)

    return TOKEN_RE.sub(_replace, pattern)


# Example patterns for reference
FORMAT_EXAMPLES = [
    {"pattern": "YYYY-MM-DD HH:mm:ss", "output": "2026-06-17 14:30:00"},
    {"pattern": "DD/MM/YYYY HH:mm", "output": "17/06/2026 14:30"},
    {"pattern": "MM-DD-YYYY", "output": "06-17-2026"},
]
