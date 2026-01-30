# config stuff
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Character:
    name: str
    aliases: Tuple[str, ...]


# update this list to match the game charcters (this is for my friends and i's psuedo dnd stuff!)
CHARACTERS: List[Character] = [
    Character("zephyr", ("zephyr",)), Character("sunset", ("sunset",)), Character("azion", ("azion",)),
    Character("yuuyi", ("yuuyi",)), Character("ciel", ("ciel",)), Character("kal", ("kal",)),
    Character("john", ("john",)), Character("cory", ("cory",)), Character("brian", ("brian",)),
    Character("jax", ("jax",)), Character("cain", ("cain",)), Character("cecilia", ("cecilia",)),
    Character("arc", ("arc",)), Character("azion", ("azion",)), Character("erik", ("erik",)), Character("shatter", ("shatter",)),
]

# grabs date from filename if it looks like 2026-01-01
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# the good vibes vs bad vibes words for mood meter
POS_WORDS = {"smile", "smiled", "laugh", "laughed", "happy", "hope", "hopeful", "relief", "safe", "calm", "win", "won", "victory", "love", "kind", "warm", "bright", "good", "nice", "okay"}
NEG_WORDS = {"blood", "bleed", "bleeding", "wound", "wounded", "hurt", "pain", "panic", "fear", "afraid", "dead", "death", "kill", "killed", "hate", "anger", "angry", "scream", "screamed", "cruel", "dark", "cold", "bad", "worse"}

# boring words skipped when pulling keywords
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z']+")
STOPWORDS = {"the", "a", "an", "and", "or", "but", "if", "then", "than", "so", "to", "of", "in", "on", "at", "for", "with", "from", "into", "out", "up", "down", "over", "under", "as", "is", "are", "was", "were", "be", "been", "being", "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "they", "we", "me", "him", "her", "them", "my", "your", "his", "hers", "their", "our", "mine", "yours", "ours", "theirs", "not", "no", "yes", "just", "very", "really", "like", "got", "get", "gets", "getting", "do", "does", "did", "doing", "have", "has", "had", "having", "will", "would", "can", "could", "should", "may", "might", "must", "also", "too", "only", "again", "all", "any", "some", "more", "most", "much", "many", "few", "each", "every", "either", "neither"}

# combat words used for tension score
COMBAT_WORDS = {"attack", "attacks", "attacked", "hit", "hits", "strike", "strikes", "struck", "stab", "stabs", "stabbed", "slash", "slashes", "slashed", "cut", "cuts", "parry", "parries", "parried", "block", "blocks", "blocked", "dodge", "dodges", "dodged", "blood", "wound", "wounds", "wounded", "kill", "kills", "killed", "dead", "fight", "fights", "fought", "battle", "battles", "combat", "spell", "spells", "cast", "casts", "casting", "arrow", "arrows", "blade", "sword", "dagger", "gun", "shot", "shots", "shoot", "shoots"}

# punctuation counted for tension
INTENSITY_CHARS = set("!?")
