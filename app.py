# dashboard ui
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from config import CHARACTERS
from helpers import heat_color, heat_tags, sparkline
from models import DashboardStats, compute_stats
from render import (
    div,
    render_cooc_heatmap,
    render_entropy_panel,
    render_meta_panel,
    render_mood_panel,
    render_top_squads,
    render_top_trios,
)
from widgets import Ticker


class ImaginationInsider(App):
    TITLE = "imagination insider"

    # styles for the layout
    CSS = """
    Screen { background: #080816; color: rgba(245,245,255,0.92); }
    .topbar { height: 1; overflow: hidden; background: #0b0b1c; padding: 0 1; content-align: left middle; }
    .ticker { height: 1; overflow: hidden; background: #0b0b1c; padding: 0 1; content-align: left middle; }
    .panel { border: tall rgba(210, 200, 255, 0.22); background: #0e0f22; padding: 0 1; }
    .dim { color: rgba(245,245,255,0.66); }
    .tag { color: rgba(245, 245, 255, 0.92); text-style: bold; padding: 0 0; }
    #layout { height: 1fr; } #bottom { height: 14; }
    #left { width: 36; } #center { width: 1fr; } #right { width: 52; }
    #center_grid { grid-size: 2; grid-gutter: 1 1; height: auto; }
    """

    BINDINGS = [
        ("q", "quit", "quit"),
        ("r", "refresh", "refresh"),
        ("up", "move_up", "up"),
        ("down", "move_down", "down"),
        ("k", "move_up", "up"),
        ("j", "move_down", "down"),
    ]

    folder: Path
    stats: DashboardStats
    selected: reactive[str] = reactive("")

    def __init__(self, folder: Path, **kwargs):
        super().__init__(**kwargs)
        self.folder = folder
        self.stats = compute_stats(folder)
        self.selected = self._pick_default_selected()
        self.top: Static
        self.ticker: Ticker
        self.hotspots: Static
        self.center_matrix: Static
        self.center_entropy: Static
        self.center_meta: Static
        self.center_mood: Static
        self.center_trios: Static
        self.center_squads: Static
        self.right_box: Static
        self.controls: Static
        self.articles: Static

    def _pick_default_selected(self) -> str:
        # pick the character with most mentions
        if not self.stats.totals:
            return CHARACTERS[0].name
        best = max(self.stats.totals.items(), key=lambda kv: kv[1])
        return best[0]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)

        self.top = Static()
        self.top.add_class("topbar")
        yield self.top
        self.ticker = Ticker()
        self.ticker.add_class("ticker")
        yield self.ticker

        with Horizontal(id="layout"):
            with Vertical(id="left", classes="panel"):
                yield Static("[ character list ]", classes="tag")
                self.hotspots = Static(classes="dim")
                yield self.hotspots
            with Vertical(id="center", classes="panel"):
                yield Static("[ relationships and meta stats ]", classes="tag")
                with Grid(id="center_grid"):
                    self.center_matrix = Static(classes="dim")
                    yield self.center_matrix
                    self.center_entropy = Static(classes="dim")
                    yield self.center_entropy
                    self.center_meta = Static(classes="dim")
                    yield self.center_meta
                    self.center_mood = Static(classes="dim")
                    yield self.center_mood
                    self.center_trios = Static(classes="dim")
                    yield self.center_trios
                    self.center_squads = Static(classes="dim")
                    yield self.center_squads
            with Vertical(id="right", classes="panel"):
                yield Static("[ intel ]", classes="tag")
                self.right_box = Static(classes="dim")
                yield self.right_box
                yield Static("")
                yield Static("[ controls ]", classes="tag")
                self.controls = Static("character: up/down (j/k)\nr refresh  q quit", classes="dim")
                yield self.controls

        with Vertical(id="bottom", classes="panel"):
            yield Static("[ articles ]", classes="tag")
            self.articles = Static(classes="dim")
            yield self.articles
        yield Footer()

    def on_mount(self) -> None:
        self._render_topbar()
        self._render_ticker()
        self._render_hotspots()
        self._render_right()
        self._render_center()
        self._render_articles()

    def _avg_tension(self) -> int:
        if not self.stats.per_file:
            return 0
        return int(round(sum(fs.tension for fs in self.stats.per_file) / len(self.stats.per_file)))

    def _ties_for(self, who: str, limit: int = 6) -> List[Tuple[str, int]]:
        ties: Dict[str, int] = {}
        for (a, b), w in self.stats.cooc.items():
            if a == who:
                ties[b] = ties.get(b, 0) + w
            elif b == who:
                ties[a] = ties.get(a, 0) + w
        return sorted(ties.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    def _top_pairs(self, limit: int = 6) -> List[Tuple[str, str, int]]:
        items = [(*k, v) for k, v in self.stats.cooc.items()]
        items.sort(key=lambda t: t[2], reverse=True)
        return items[:limit]

    def _top_keywords_for(self, who: str, limit: int = 10) -> List[Tuple[str, int]]:
        counts = self.stats.keywords.get(who, {})
        out = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        char_names = {c.name for c in CHARACTERS}
        return [(w, n) for (w, n) in out if w not in char_names][:limit]

    def _render_topbar(self) -> None:
        self.top.update("[b]imagination insider[/b] | made with love (and hate) by jax")

    def _render_ticker(self) -> None:
        totals_sorted = sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)
        top = [f"{k}:{v}" for k, v in totals_sorted[:6]]

        files = [f"ingested {fs.filename}" for fs in self.stats.per_file[-3:]]
        self.ticker.set_items(["imagination insider", *top, *files])

    def _render_hotspots(self) -> None:
        # character list with heat bars
        totals_sorted = sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)
        max_count = totals_sorted[0][1] if totals_sorted else 0
        lines = []
        for i, (name, count) in enumerate(totals_sorted, start=1):
            if name == self.selected:
                prefix = "[#e9ecff]›[/]"
            else:
                prefix = " "
            tags = heat_tags(count, max_count, width=14)
            lines.append(f"{prefix} {i:>2}. {name:<12}  {tags}  [#cbb7ff]{count}[/]")
        self.hotspots.update("\n".join(lines) if lines else "[#6f7398]no data[/]")

    def _render_center(self) -> None:
        totals_sorted = sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)
        top_names = [name for name, _ in totals_sorted[:12]]
        w = self.center_matrix.size.width or 80
        self.center_matrix.update(render_cooc_heatmap(cooc=self.stats.cooc, names=top_names, selected=self.selected, max_width=w))
        self.center_entropy.update(render_entropy_panel(self.stats))
        self.center_meta.update(render_meta_panel(self.stats))
        self.center_mood.update(render_mood_panel(self.stats))
        self.center_trios.update(render_top_trios(self.stats, limit=6))
        self.center_squads.update(render_top_squads(self.stats, limit=5))

    def _render_right(self) -> None:
        total = self.stats.totals.get(self.selected, 0)
        totals_sorted = sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)

        max_total = totals_sorted[0][1] if totals_sorted else 0
        ratio = (total / max_total) if max_total > 0 else 0.0
        hc = heat_color(ratio)

        if self.selected == "kal":
            if ratio < 0.30:
                label = "kool"
            elif ratio < 0.55:
                label = "keen"
            else:
                label = "khaotic"
        else:
            if ratio >= 0.55:
                label = "hot"
            elif ratio >= 0.30:
                label = "warm"
            else:
                label = "cool"

        series = [m.get(self.selected, 0) for _, m in self.stats.trend]
        sp = sparkline(series, width=24)
        latest_chapter = series[-1] if series else 0
        latest_file = self.stats.per_file[-1] if self.stats.per_file else None
        if latest_file and latest_file.session_tensions:
            latest_tension, tension_note = latest_file.session_tensions[-1], "latest session"
        else:
            latest_tension = latest_file.tension if latest_file else 0
            tension_note = "latest file"

        avg_tension = self._avg_tension()
        tcol = "#ffb3c1" if latest_tension >= 70 else "#ffd6a5" if latest_tension >= 45 else "#b8f2b2"
        acol = "#ffb3c1" if avg_tension >= 70 else "#ffd6a5" if avg_tension >= 45 else "#b8f2b2"
        ties = self._ties_for(self.selected, limit=6)
        top_pairs = self._top_pairs(limit=5)
        kws = self._top_keywords_for(self.selected, limit=10)

        lines: List[str] = [
            f"[b]{self.selected}[/b]  [{hc}]{label}[/]",
            f"[#cbb7ff]mentions[/] {total}  [#cbb7ff]latest chapter[/] {latest_chapter}",
            f"[#cbb7ff]trend[/] {sp}",
            f"[#cbb7ff]tension[/] {tension_note} [{tcol}]{latest_tension}[/]/100  avg [{acol}]{avg_tension}[/]/100",
            "", div(f"ties for {self.selected}"),
        ]
        if not ties:
            lines.append("  [#6f7398]none[/]")
        else:
            mx = max((w for _, w in ties), default=1)
            lines.extend(f"  {other:<10} [{heat_color(wgt / mx if mx else 0.0)}]{wgt}[/]" for other, wgt in ties)

        lines.extend(["", div("strongest ties overall")])
        if not top_pairs:
            lines.append("  [#6f7398]none[/]")
        else:
            mx2 = max((w for _, _, w in top_pairs), default=1)
            lines.extend(f"  {a} ↔ {b}  [{heat_color(wgt / mx2 if mx2 else 0.0)}]{wgt}[/]" for a, b, wgt in top_pairs)

        lines.extend(["", div("keywords")])
        if not kws:
            lines.append("  [#6f7398]none[/]")
        else:
            mxk = max((n for _, n in kws), default=1)
            chunk = [f"[{heat_color(n / mxk if mxk else 0.0)}]{wword}[/]([#9fe7ff]{n}[/])" for wword, n in kws[:10]]
            lines.append("  " + "  ".join(chunk))
        self.right_box.update("\n".join(lines))

    def _render_articles(self) -> None:
        blocks = []

        for fs in reversed(self.stats.per_file[-6:]):
            lines = fs.lines_for_selected.get(self.selected, [])
            if not lines:
                continue
            head = f"[#9fe7ff]{fs.filename}[/] [#6f7398](words {fs.words}, tension {fs.tension}, sessions {fs.session_count})[/]"
            blocks.append(head + "\n" + "\n".join(f"  - {ln}" for ln in lines[:6]))

        self.articles.update("\n\n".join(blocks) if blocks else "[#6f7398]no mentions found for selected character in recent files[/]")

    def action_refresh(self) -> None:
        self.stats = compute_stats(self.folder)
        if self.selected not in self.stats.totals:
            self.selected = self._pick_default_selected()
        self._render_topbar()
        self._render_ticker()
        self._render_hotspots()
        self._render_right()
        self._render_center()
        self._render_articles()

    def action_move_up(self) -> None:
        totals_sorted = [k for k, _ in sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)]
        if not totals_sorted:
            return
        idx = totals_sorted.index(self.selected) if self.selected in totals_sorted else 0
        self.selected = totals_sorted[max(0, idx - 1)]
        self._render_hotspots()
        self._render_right()
        self._render_center()
        self._render_articles()

    def action_move_down(self) -> None:
        totals_sorted = [k for k, _ in sorted(self.stats.totals.items(), key=lambda kv: kv[1], reverse=True)]
        if not totals_sorted:
            return
        idx = totals_sorted.index(self.selected) if self.selected in totals_sorted else 0
        self.selected = totals_sorted[min(len(totals_sorted) - 1, idx + 1)]
        self._render_hotspots()
        self._render_right()
        self._render_center()
        self._render_articles()

    def action_quit(self) -> None:
        self.exit()
