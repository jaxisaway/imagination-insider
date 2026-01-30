# helper functions for text and stats
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

from config import (
    COMBAT_WORDS,
    DATE_RE,
    INTENSITY_CHARS,
    NEG_WORDS,
    POS_WORDS,
    STOPWORDS,
    _WORD_RE,
)


def clamp(value: int, low: int, high: int) -> int:
    # keep value between low and high
    if value < low:
        return low
    if value > high:
        return high
    return value


def normalize(text: str) -> str:
    # fix line endings and curly quotes
    text = text.replace("\r\n", "\n")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return text


def parse_date_from_filename(name: str) -> str:
    # pluck date if filename looks like yyyy-mm-dd
    match = DATE_RE.search(name)
    if match:
        return match.group(1)
    return "unknown"


def read_txt(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return normalize(raw)


def heat_color(ratio: float) -> str:
    # pick a colour based on how big the ratio is (for heat bars)
    if ratio >= 0.80:
        return "#ffb3c1"
    if ratio >= 0.55:
        return "#ffd6a5"
    if ratio >= 0.30:
        return "#fff2a8"
    return "#b8f2b2"


def heat_tags(count: int, max_count: int, width: int = 14) -> str:
    if max_count <= 0:
        filled = 0
        ratio = 0.0
    else:
        ratio = count / max_count
        filled = int(round(ratio * width))
        filled = clamp(filled, 0, width)

    empty = width - filled
    color = heat_color(ratio)
    return f"[{color}]" + ("#" * filled) + "[/]" + "[#5c607f]" + ("·" * empty) + "[/]"


def sparkline(values: List[int], width: int = 26) -> str:
    # turns numbers into little block characters (the mini bar chart thing)
    blocks = "▁▂▃▄▅▆▇█"
    if not values:
        return ""

    valmin = values[0]
    for val in values:
        if val < valmin:
            valmin = val
    valmax = values[0]
    for val in values:
        if val > valmax:
            valmax = val

    if valmax == valmin:
        blockcount = width
        if len(values) < blockcount:
            blockcount = len(values)
        return blocks[0] * blockcount

    start = len(values) - width
    if start < 0:
        start = 0

    out = []
    for i in range(start, len(values)):
        val = values[i]
        normalized = (val - valmin) / (valmax - valmin)
        blockidx = int(round(normalized * (len(blocks) - 1)))
        blockidx = clamp(blockidx, 0, len(blocks) - 1)
        out.append(blocks[blockidx])

    return "".join(out)


def tokenize(text: str) -> List[str]:
    # get words from text, skip short ones
    result = []
    for match in _WORD_RE.finditer(text):
        word = match.group(0).lower()
        if len(word) >= 3:
            result.append(word)
    return result


def calc_tension(text: str) -> int:
    # rough tension score 0 to 100
    if not text.strip():
        return 0

    lines = []
    for line in text.splitlines():
        if line.strip():
            lines.append(line)
    if not lines:
        return 0

    joined = "\n".join(lines)
    total_chars = len(joined)
    if total_chars < 1:
        total_chars = 1

    punct = 0
    for ch in INTENSITY_CHARS:
        punct = punct + joined.count(ch)
    punct_rate = punct / total_chars

    words = tokenize(joined)
    total_words = len(words)
    if total_words < 1:
        total_words = 1
    combathits = 0
    for word in words:
        if word in COMBAT_WORDS:
            combathits = combathits + 1
    combat_rate = combathits / total_words

    caps = 0
    for ch in joined:
        if ch.isupper():
            caps = caps + 1
    caps_rate = caps / total_chars
    shortlines = 0
    for line in lines:
        if len(line) <= 60:
            shortlines = shortlines + 1
    pace = shortlines / len(lines)

    # mash it all together into one score (punct + combat + caps + pace)
    p1 = int(punct_rate * 6000)
    p1 = clamp(p1, 0, 100)
    part1 = 55 * p1 / 100.0

    p2 = int(combat_rate * 900)
    p2 = clamp(p2, 0, 100)
    part2 = 70 * p2 / 100.0

    p3 = int(caps_rate * 2500)
    p3 = clamp(p3, 0, 100)
    part3 = 35 * p3 / 100.0

    part4 = 25 * pace
    score = part1 + part2 + part3 + part4

    final = int(round(score))
    return clamp(final, 0, 100)


def build_alias_regex(aliases: Tuple[str, ...]) -> List[re.Pattern[str]]:
    # one regex per alias so we dont match "sunset" inside "sunsetter" or whatever
    result = []
    for alias in aliases:
        result.append(re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE))
    return result


def count_mentions(text: str, alias_patterns: List[re.Pattern[str]]) -> int:
    # count how many times any of the patterns match in text
    total = 0
    for pattern in alias_patterns:
        total += len(pattern.findall(text))
    return total


def extract_lines_with_mentions(text: str, alias_patterns: List[re.Pattern[str]], limit: int = 12) -> List[str]:
    # grab lines that mention someone, cap at limit so we dont return a novel
    out = []
    for line in text.splitlines():
        found = False
        for pattern in alias_patterns:
            if pattern.search(line):
                found = True
                break
        if found:
            cleaned = line.strip()
            if cleaned:
                out.append(cleaned[:180])
        if len(out) >= limit:
            break
    return out


def div(title: str = "") -> str:
    # divider line for the ui, optional title in the middle
    if title:
        return f"[#6f7398]──── {title} ────[/]"
    return "[#6f7398]────────────────────[/]"


# line that is just dashes (session separator)
_DASH_SEP_RE = re.compile(r"^\s*[-–—]{3,}\s*$")


def _chunk_has_content(chunk: List[str]) -> bool:
    for line in chunk:
        if line.strip():
            return True
    return False


def split_sessions(text: str) -> List[str]:
    # sessions are split by --- or by 2+ blank lines
    lines = text.splitlines()
    out = []
    cur = []
    blank_run = 0

    for line in lines:
        if _DASH_SEP_RE.match(line):
            if _chunk_has_content(cur):
                out.append(cur)
            cur = []
            blank_run = 0
            continue
        if not line.strip():
            blank_run = blank_run + 1
            cur.append(line)
            if blank_run >= 2:
                if _chunk_has_content(cur):
                    out.append(cur)
                cur = []
                blank_run = 0
            continue
        blank_run = 0
        cur.append(line)

    if _chunk_has_content(cur):
        out.append(cur)

    sessions = []
    for chunk in out:
        s = "\n".join(chunk).strip()
        if s:
            sessions.append(s)
    return sessions


def shannon_entropy(counts: Dict[str, int]) -> float:
    # how spread out the counts are, 0 = one person dominates, 1 = everyone equal
    vals = []
    for val in counts.values():
        if val > 0:
            vals.append(val)
    if not vals:
        return 0.0

    total = 0
    for val in vals:
        total = total + val
    if total <= 0:
        return 0.0

    probabilities = []
    for val in vals:
        if val > 0:
            probabilities.append(val / total)

    entropy = 0
    for prob in probabilities:
        if prob > 0:
            entropy = entropy - (prob * math.log(prob, 2))

    if len(probabilities) > 1:
        maxentropy = math.log(len(probabilities), 2)
    else:
        maxentropy = 1.0

    if maxentropy > 0:
        raw = (entropy / maxentropy) * 1000
    else:
        raw = 0
    raw = clamp(int(round(raw)), 0, 1000)
    return float(raw / 1000.0)


def entropy_bar(x: float, width: int = 10) -> str:
    if x < 0.0:
        x = 0.0
    elif x > 1.0:
        x = 1.0
    filled = int(round(x * width))
    filled = clamp(filled, 0, width)

    empty = width - filled
    color = heat_color(x)
    return f"[{color}]" + ("█" * filled) + "[/]" + "[#3b3f5c]" + ("·" * empty) + "[/]"


def entropy_spark(values: List[float], width: int = 7) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    if not values:
        return ""

    valmin = values[0]
    for val in values:
        if val < valmin:
            valmin = val
    valmax = values[0]
    for val in values:
        if val > valmax:
            valmax = val

    if valmax == valmin:
        blockcount = width
        if len(values) < blockcount:
            blockcount = len(values)
        return blocks[0] * blockcount

    start = len(values) - width
    if start < 0:
        start = 0

    out = []
    for i in range(start, len(values)):
        val = values[i]
        normalized = (val - valmin) / (valmax - valmin)
        blockidx = int(round(normalized * (len(blocks) - 1)))
        blockidx = clamp(blockidx, 0, len(blocks) - 1)
        out.append(blocks[blockidx])

    return "".join(out)
