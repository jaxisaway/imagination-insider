# the ticker widget i love this thing
from __future__ import annotations

from typing import List

from textual.reactive import reactive
from textual.widgets import Static


class Ticker(Static):
    # scrolls through a list of strings
    offset = reactive(0)

    def __init__(self) -> None:
        super().__init__()
        self.items: List[str] = []
        self._tick = 0
        self.can_focus = False

    def set_items(self, items: List[str]) -> None:
        # swap in new items and reset scroll
        self.items = items
        self.offset = 0
        self._tick = 0
        self.refresh()

    def on_mount(self) -> None:
        self.set_interval(0.12, self.step)

    def step(self) -> None:
        # move the scroll position and update the display
        if not self.items:
            self.update("[b][#cbb7ff]news[/] [#e9ecff]no signals yet[/][/b]")
            return

        # double the text so we can wrap around when scrolling
        text = "   +++   ".join(self.items) + "   +++   "
        self._tick = (self._tick + 1) % max(1, len(text))
        self.offset = self._tick

        width = self.size.width or 80
        payloadwidth = max(10, width - 7)
        payload = (text + text)[self.offset : self.offset + payloadwidth]
        payload = payload.replace("\n", " ").replace("\t", " ")[:payloadwidth]
        self.update(f"[b][#cbb7ff]news[/] [#e9ecff]{payload}[/][/b]")
