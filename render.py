# drawing the panels (heatmap, meta, mood, etc)
from __future__ import annotations

from typing import Dict, List, Tuple

from helpers import div, entropy_bar, entropy_spark, heat_color, shannon_entropy
from models import DashboardStats


def _abbr(name: str) -> str:
    # shorten name to 2 letters for the heatmap labels
    name = (name or "").lower()
    if len(name) == 1:
        return (name + " ").upper()
    if len(name) == 2:
        return name.upper()
    return (name[0] + name[1]).upper()


def render_cooc_heatmap(cooc: Dict[Tuple[str, str], int], names: List[str], selected: str, max_width: int) -> str:
    # draw the co-occurrence matrix as a little heatmap
    if not names:
        return "[#6f7398]no matrix data[/]"

    namecount = len(names)
    needed = 3 + namecount * 3
    if needed > max_width:
        maxnames = max(3, (max_width - 3) // 3)
        names = names[:maxnames]
        namecount = len(names)

    # build the matrix, fill from cooc data
    matrix = []
    for i in range(namecount):
        row = []
        for j in range(namecount):
            row.append(0)
        matrix.append(row)

    nameidx = {}
    for i in range(namecount):
        nameidx[names[i]] = i
    for (char_a, char_b), weight in cooc.items():
        if char_a in nameidx and char_b in nameidx:
            rowidx, colidx = nameidx[char_a], nameidx[char_b]
            matrix[rowidx][colidx] = weight
            matrix[colidx][rowidx] = weight

    rowmax = []
    for i in range(namecount):
        biggest = 0
        for j in range(namecount):
            if matrix[i][j] > biggest:
                biggest = matrix[i][j]
        rowmax.append(biggest)
    headerparts = []
    for name in names:
        headerparts.append(_abbr(name))
    header = "   " + " ".join(headerparts)
    lines = [f"[#cbb7ff]{header}[/]"]

    for i in range(len(names)):
        rowname = names[i]
        rowlabel = _abbr(rowname)
        rowcells: List[str] = []
        for j in range(namecount):
            if i == j:
                cell = "[#cbb7ff]██[/]"
            else:
                weight = matrix[i][j]
                if weight <= 0:
                    cell = "[#3b3f5c]··[/]"
                else:
                    selectedidx = None
                    if selected in nameidx:
                        selectedidx = nameidx[selected]
                    if selectedidx is not None and (i == selectedidx or j == selectedidx):
                        denom = rowmax[selectedidx]
                    else:
                        if rowmax[i] > rowmax[j]:
                            denom = rowmax[i]
                        else:
                            denom = rowmax[j]
                    if denom > 0:
                        ratio = weight / denom
                    else:
                        ratio = 0.0
                    cell = f"[{heat_color(ratio)}]██[/]"
            if rowname == selected or names[j] == selected:
                cell = f"[b]{cell}[/b]"
            rowcells.append(cell)
        if rowname == selected:
            labelcolor = "#e9ecff"
        else:
            labelcolor = "#9fe7ff"
        lines.append(f"[{labelcolor}]{rowlabel}[/] " + " ".join(rowcells))
    return "\n".join(lines)


# picks low/mid/high based on how much evidence we have
def _tier(intensity: int, low: str, mid: str, high: str) -> str:
    if intensity >= 18:
        return high
    if intensity >= 8:
        return mid
    return low


def sentiment_label(pos: int, neg: int) -> Tuple[str, str]:
    # mood label and colour from pos/neg word ratio
    total = pos + neg
    if total <= 0:
        return ("blank", "#6f7398")

    score = (pos - neg) / total
    intensity = total

    if score >= 0.70:
        return (_tier(intensity, "good", "uplifted", "euphoric"), "#b8f2b2")
    if score >= 0.45:
        return (_tier(intensity, "okay", "hopeful", "radiant"), "#b8f2b2")
    if score >= 0.25:
        return (_tier(intensity, "calm", "warm", "confident"), "#fff2a8")
    if score >= 0.10:
        return (_tier(intensity, "steady", "content", "relieved"), "#fff2a8")
    if score > -0.10:
        return (_tier(intensity, "mixed", "unclear", "volatile"), "#ffd6a5")
    if score > -0.25:
        return (_tier(intensity, "tense", "uneasy", "anxious"), "#ffd6a5")
    if score > -0.45:
        return (_tier(intensity, "grim", "strained", "fraying"), "#ffd6a5")
    if score > -0.70:
        return (_tier(intensity, "sad", "dread", "panicked"), "#ffb3c1")
    return (_tier(intensity, "bad", "bleak", "catastrophic"), "#ffb3c1")


def render_meta_panel(stats: DashboardStats) -> str:
    # meta stats (files, words, lines, etc)
    if not stats.per_file:
        return "[#6f7398]no files loaded[/]"
    filescount = len(stats.per_file)
    totalwords = 0
    totallines = 0
    totalchars = 0
    totalcaps = 0
    exclaimcount = 0
    questioncount = 0
    sessionstotal = 0

    for filestats in stats.per_file:
        totalwords = totalwords + filestats.words
        totallines = totallines + filestats.lines
        totalchars = totalchars + filestats.chars
        totalcaps = totalcaps + filestats.caps
        exclaimcount = exclaimcount + filestats.exclaims
        questioncount = questioncount + filestats.questions
        sessionstotal = sessionstotal + filestats.session_count

    if totallines > 0:
        avglinelen = int(round(totalchars / totallines))
    else:
        avglinelen = 0
    if totalchars > 0:
        capsrate = (totalcaps / totalchars) * 100.0
    else:
        capsrate = 0.0

    return f"{div('meta stats')}\n[#cbb7ff]files[/] {filescount}   [#cbb7ff]sessions[/] {sessionstotal}\n[#cbb7ff]words[/] {totalwords}   [#cbb7ff]lines[/] {totallines}\n[#cbb7ff]avg line len[/] {avglinelen}   [#cbb7ff]caps[/] {capsrate:.1f}%\n[#cbb7ff]![/] {exclaimcount}   [#cbb7ff]?[/] {questioncount}"


def _latest_session_entropies(stats: DashboardStats, sessioncount: int = 10) -> List[float]:
    # get entropy for last n sessions
    out = []
    for filestats in stats.per_file:
        for sessionmentions in filestats.session_mentions:
            out.append(shannon_entropy(sessionmentions))
    start = len(out) - sessioncount
    if start < 0:
        start = 0
    result = []
    for i in range(start, len(out)):
        result.append(out[i])
    return result


def _latest_session_sentiment(stats: DashboardStats, sessioncount: int = 10) -> Tuple[int, int]:
    # sum pos/neg for last n sessions
    poslist = []
    neglist = []
    for filestats in stats.per_file:
        for i in range(len(filestats.session_pos)):
            poslist.append(filestats.session_pos[i])
            neglist.append(filestats.session_neg[i])

    start = len(poslist) - sessioncount
    if start < 0:
        start = 0
    possum = 0
    for i in range(start, len(poslist)):
        possum = possum + poslist[i]

    start = len(neglist) - sessioncount
    if start < 0:
        start = 0
    negsum = 0
    for i in range(start, len(neglist)):
        negsum = negsum + neglist[i]

    return (possum, negsum)


def render_mood_panel(stats: DashboardStats) -> str:
    # mood meter from pos/neg words
    if not stats.per_file:
        return f"{div('mood meter')}\n[#6f7398]no files[/]"

    pos_all = 0
    neg_all = 0
    for filestats in stats.per_file:
        pos_all = pos_all + filestats.pos
        neg_all = neg_all + filestats.neg
    labelall, colorall = sentiment_label(pos_all, neg_all)
    if pos_all + neg_all == 0:
        totalmix = "no signals"
    else:
        totalmix = f"+{pos_all} / -{neg_all}"
    pos10, neg10 = _latest_session_sentiment(stats, sessioncount=10)
    label10, color10 = sentiment_label(pos10, neg10)
    if pos10 + neg10 == 0:
        tenmix = "no signals"
    else:
        tenmix = f"+{pos10} / -{neg10}"

    lastfile = stats.per_file[-1]
    if lastfile.session_pos and lastfile.session_neg:
        lastpos, lastneg = lastfile.session_pos[-1], lastfile.session_neg[-1]
        labellast, colorlast = sentiment_label(lastpos, lastneg)
        latestline = f"[#cbb7ff]latest session[/]  [{colorlast}]{labellast}[/]  [#6f7398](+{lastpos} / -{lastneg})[/]"
    else:
        labellast, colorlast = sentiment_label(lastfile.pos, lastfile.neg)
        latestline = f"[#cbb7ff]latest file[/]     [{colorlast}]{labellast}[/]  [#6f7398](+{lastfile.pos} / -{lastfile.neg})[/]"

    return f"{div('mood meter')}\n[#cbb7ff]overall[/] [{colorall}]{labelall}[/]  [#6f7398]({totalmix})[/]\n[#cbb7ff]past 10 sessions[/] [{color10}]{label10}[/]  [#6f7398]({tenmix})[/]\n{latestline}\n[#6f7398]positive to negative word ratio[/]"


def _entropy_label(value: float) -> Tuple[str, str]:
    if value >= 0.90:
        return ("meltdown", "#ffb3c1")
    if value >= 0.80:
        return ("frenzied", "#ffb3c1")
    if value >= 0.70:
        return ("restless", "#ffd6a5")
    if value >= 0.60:
        return ("turbulent", "#ffd6a5")
    if value >= 0.50:
        return ("scattered", "#ffd6a5")
    if value >= 0.40:
        return ("unsteady", "#fff2a8")
    if value >= 0.30:
        return ("dialed-in", "#fff2a8")
    if value >= 0.20:
        return ("grounded", "#b8f2b2")
    if value >= 0.10:
        return ("still", "#b8f2b2")
    return ("sealed", "#b8f2b2")


def render_entropy_panel(stats: DashboardStats) -> str:
    # entropy meter (how spread out mentions are)
    if not stats.per_file:
        return f"{div('entropy meter')}\n[#6f7398]no data[/]"

    entropies = _latest_session_entropies(stats, sessioncount=10)
    if not entropies:
        return f"{div('entropy meter')}\n[#6f7398]no sessions detected[/]"

    latestentropy = entropies[-1]
    avg10 = 0
    for val in entropies:
        avg10 = avg10 + val
    avg10 = avg10 / len(entropies)

    sparkstr = entropy_spark(entropies, width=10)
    baravg = entropy_bar(avg10, width=10)
    barlatest = entropy_bar(latestentropy, width=10)

    labellatest, colorlatest = _entropy_label(latestentropy)
    labelavg, coloravg = _entropy_label(avg10)

    return f"{div('entropy meter')}\n[#cbb7ff]latest 10 sessions[/]  [#e9ecff]{sparkstr}[/]\n{baravg}  [#cbb7ff]{avg10:.2f}[/]  [{coloravg}]{labelavg}[/]  [#6f7398]avg(10)[/]\n{barlatest}  [#cbb7ff]{latestentropy:.2f}[/]  [{colorlatest}]{labellatest}[/]  [#6f7398]latest session[/]\n[#6f7398]higher = attent. spread across more characters (more chaos)[/]"


def render_top_trios(stats: DashboardStats, limit: int = 6) -> str:
    # top character trios (3 together)
    if not stats.trios:
        return f"{div('top trios')}\n[#6f7398]none detected[/]"

    # sort by count (biggest first) then take top few
    pairs = []
    for key, weight in stats.trios.items():
        pairs.append((weight, key))
    pairs.sort()
    pairs.reverse()

    items = []
    for i in range(min(limit, len(pairs))):
        items.append((pairs[i][1], pairs[i][0]))

    maxweight = 1
    for _, weight in items:
        if weight > maxweight:
            maxweight = weight

    lines = [div("top trios")]
    for trio, weight in items:
        ratio = weight / maxweight
        if maxweight == 0:
            ratio = 0.0
        char_a = trio[0]
        char_b = trio[1]
        char_c = trio[2]
        lines.append("  " + char_a + "+" + char_b + "+" + char_c + "  [" + heat_color(ratio) + "]" + str(weight) + "[/]")
    return "\n".join(lines)


def render_top_squads(stats: DashboardStats, limit: int = 6) -> str:
    # top character squads (4 together)
    if not stats.squads:
        return f"{div('top squads')}\n[#6f7398]none detected[/]"

    pairs = []
    for key, weight in stats.squads.items():
        pairs.append((weight, key))
    pairs.sort()
    pairs.reverse()

    items = []
    for i in range(min(limit, len(pairs))):
        items.append((pairs[i][1], pairs[i][0]))

    maxweight = 1
    for _, weight in items:
        if weight > maxweight:
            maxweight = weight

    lines = [div("top squads")]
    for squad, weight in items:
        ratio = weight / maxweight
        if maxweight == 0:
            ratio = 0.0
        squadstr = ""
        for i in range(len(squad)):
            if i > 0:
                squadstr = squadstr + "+"
            squadstr = squadstr + squad[i]
        lines.append("  " + squadstr + "  [" + heat_color(ratio) + "]" + str(weight) + "[/]")
    return "\n".join(lines)
