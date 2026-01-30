# data structures and the main stats
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from config import CHARACTERS, NEG_WORDS, POS_WORDS, STOPWORDS
from helpers import (
    build_alias_regex,
    calc_tension,
    count_mentions,
    extract_lines_with_mentions,
    parse_date_from_filename,
    read_txt,
    split_sessions,
    tokenize,
)


@dataclass
class FileStats:
    filename: str
    date: str
    words: int
    lines: int
    tension: int
    mentions: Dict[str, int]
    lines_for_selected: Dict[str, List[str]]
    pos: int
    neg: int
    exclaims: int
    questions: int
    caps: int
    chars: int
    text: str
    session_count: int
    session_tensions: List[int]
    session_pos: List[int]
    session_neg: List[int]
    session_mentions: List[Dict[str, int]]


@dataclass
class DashboardStats:
    totals: Dict[str, int]
    per_file: List[FileStats]
    trend: List[Tuple[str, Dict[str, int]]]
    cooc: Dict[Tuple[str, str], int]
    keywords: Dict[str, Dict[str, int]]
    trios: Dict[Tuple[str, str, str], int]
    squads: Dict[Tuple[str, str, str, str], int]


def compute_stats(folder: Path) -> DashboardStats:
    # gets all those stupid files and sorts them by name
    allpaths = []
    for path in folder.iterdir():
        if path.is_file():
            allpaths.append(path)

    # pair up (name, path) so we can sort by name
    filepairs = []
    for path in allpaths:
        filepairs.append((path.name.lower(), path))
    filepairs.sort()

    files = []
    for _, path in filepairs:
        files.append(path)

    # build regex for each character so we can find mentions
    patterns = {}
    for character in CHARACTERS:
        patterns[character.name] = build_alias_regex(character.aliases)
    totals = {}
    for character in CHARACTERS:
        totals[character.name] = 0
    perfiles = []
    cooc = {}
    keywords = {}
    for character in CHARACTERS:
        keywords[character.name] = {}
    trios = {}
    squads = {}

    # now chew through each txt file
    for filepath in files:
        if filepath.suffix.lower() != ".txt":
            continue
        text = read_txt(filepath)
        words = len(re.findall(r"\b\w+\b", text))
        alllines = text.splitlines()
        nonemptylines = []
        for line in alllines:
            if line.strip():
                nonemptylines.append(line)
        linescount = len(nonemptylines)
        tension = calc_tension(text)
        exclaims = text.count("!")
        questions = text.count("?")
        caps = 0
        for ch in text:
            if ch.isupper():
                caps = caps + 1
        chars_n = len(text)
        # count positive and negative words
        pos = 0
        for t in tokenize(text):
            if t in POS_WORDS:
                pos += 1
        neg = 0
        for t in tokenize(text):
            if t in NEG_WORDS:
                neg += 1

        # chop into sessions, get per-session stats
        sessions = split_sessions(text)
        session_tensions: List[int] = []
        session_pos: List[int] = []
        session_neg: List[int] = []
        session_mentions: List[Dict[str, int]] = []

        for sessiontext in sessions:
            session_tensions.append(calc_tension(sessiontext))
            sessionpos = 0
            for token in tokenize(sessiontext):
                if token in POS_WORDS:
                    sessionpos += 1
            sessionneg = 0
            for token in tokenize(sessiontext):
                if token in NEG_WORDS:
                    sessionneg += 1
            session_pos.append(sessionpos)
            session_neg.append(sessionneg)
            sessionmentions: Dict[str, int] = {}
            for character in CHARACTERS:
                sessionmentions[character.name] = count_mentions(sessiontext, patterns[character.name])
            session_mentions.append(sessionmentions)

        mentions: Dict[str, int] = {}
        linesforselected: Dict[str, List[str]] = {}
        for character in CHARACTERS:
            mentioncount = count_mentions(text, patterns[character.name])
            mentions[character.name] = mentioncount
            totals[character.name] += mentioncount
            linesforselected[character.name] = extract_lines_with_mentions(text, patterns[character.name], limit=14)

        # who shows up together on each line -> cooc, trios, squads, keywords
        for line in nonemptylines:
            present = []
            for character in CHARACTERS:
                found = False
                for pattern in patterns[character.name]:
                    if pattern.search(line):
                        found = True
                        break
                if found:
                    present.append(character.name)
            if not present:
                continue
            present = sorted(set(present))
            # count pairs (2 together)
            if len(present) >= 2:
                for i in range(len(present)):
                    for j in range(i + 1, len(present)):
                        key = (present[i], present[j])
                        if key in cooc:
                            cooc[key] = cooc[key] + 1
                        else:
                            cooc[key] = 1
            # count trios (3 together)
            if len(present) >= 3:
                for i in range(len(present)):
                    for j in range(i + 1, len(present)):
                        for k in range(j + 1, len(present)):
                            key3 = (present[i], present[j], present[k])
                            if key3 in trios:
                                trios[key3] = trios[key3] + 1
                            else:
                                trios[key3] = 1
            # count squads (4 together)
            if len(present) >= 4:
                for i in range(len(present)):
                    for j in range(i + 1, len(present)):
                        for k in range(j + 1, len(present)):
                            for m in range(k + 1, len(present)):
                                key4 = (present[i], present[j], present[k], present[m])
                                if key4 in squads:
                                    squads[key4] = squads[key4] + 1
                                else:
                                    squads[key4] = 1
            # grab keywords for each character on this line (skip stopwords and their own name)
            tokens = tokenize(line)
            if tokens:
                for charname in present:
                    keywordbag = keywords[charname]
                    for token in tokens:
                        if token in STOPWORDS or token == charname:
                            continue
                        if token in keywordbag:
                            keywordbag[token] = keywordbag[token] + 1
                        else:
                            keywordbag[token] = 1

        filestats = FileStats(
            filename=filepath.name,
            date=parse_date_from_filename(filepath.name),
            words=words,
            lines=linescount,
            tension=tension,
            mentions=mentions,
            lines_for_selected=linesforselected,
            pos=pos,
            neg=neg,
            exclaims=exclaims,
            questions=questions,
            caps=caps,
            chars=chars_n,
            text=text,
            session_count=len(sessions),
            session_tensions=session_tensions,
            session_pos=session_pos,
            session_neg=session_neg,
            session_mentions=session_mentions,
        )
        perfiles.append(filestats)

    # smoosh everything into trend by date
    trendmap: Dict[str, Dict[str, int]] = {}
    for filestats in perfiles:
        datestr = filestats.date
        if datestr not in trendmap:
            trendmap[datestr] = {}
            for character in CHARACTERS:
                trendmap[datestr][character.name] = 0
        for character in CHARACTERS:
            trendmap[datestr][character.name] += filestats.mentions[character.name]

    trenddates = list(trendmap.keys())
    trenddates.sort()
    trend = []
    for date in trenddates:
        trend.append((date, trendmap[date]))

    return DashboardStats(totals=totals, per_file=perfiles, trend=trend, cooc=cooc, keywords=keywords, trios=trios, squads=squads)
