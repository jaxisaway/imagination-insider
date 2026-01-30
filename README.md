# imagination insider

a terminal cli (commmand line interface) (dashboard) for text-based game logs (like d&d recaps, stories, and more!) it tracks who gets mentioned, who shows up together, the mood, tension, and more. if you write collaborative stories or run ttrpg sessions and keep logs in text files, this might pique your interest ;)

## step 1: make sure you have python (lol)

imagination insider runs on python. you need python 3.10 or newer

### how to check

open a terminal (or command prompt on windows) and type:

```bash
python --version
```

or sometimes it's:

```bash
python3 --version
```

you should see something like `Python 3.10.0` or higher. if you get "command not found" or an error, you need to install python first. go do that!

## step 2: get the imagination insider folder

download or clone this repo so you have a folder with all the files in it. the main file you'll run is called `imagination_insider.py`

## step 3: install the thing it needs (textual)

imagination insider uses a library called textual to draw the interface. you only need to do this once

open a terminal, go to the imagination insider folder, then run:

```bash
pip install textual
```

or if that doesn't work:

```bash
pip3 install textual
```

### what does "go to the folder" mean?

you need to be *in* the imagination insider folder when you run commands:

**windows (command prompt or powershell):**
```cmd
cd C:\Users\YourName\Downloads\imagination-insider
```
(or whatever the path is)

**mac / linux:**
```bash
cd ~/Downloads/imagination-insider
```
(or wherever you put the folder)

you'll know you're in the right place when you type `dir` (windows) or `ls` (mac/linux) and you see `imagination_insider.py` in the list

## step 4: put your log files somewhere

imagination insider reads `.txt` files from a folder. all your game logs or session notes need to be in one folder, and they need to end in `.txt`

example:

```
my_game_logs/
  session_2026_01_01.txt
  session_2026_01_02.txt
  session_2026_01_03.txt
```

that's it. just plain text files. you can name them whatever you want as long as they end in `.txt`

### optional: dates in filenames

if you put a date in the filename like `2026-01-01`, the cli can show you trends over time. not required though

### optional: splitting sessions inside one file

if one file has multiple sessions, separate them with a line of dashes:

```
--- session 1 stuff ---

--- session 2 stuff ---
```

or use 2 or more blank lines in a row. it'll count them as separate sessions

## step 5: run that thang

from the imagination insider folder (the one with `imagination_insider.py` in it), run:

```bash
python imagination_insider.py
```

that's it. if you've never run it before, it will look for a folder called `game_logs` inside your home directory. if that doesn't exist, it might cause an error. in that case, tell it where your logs are:

```bash
python imagination_insider.py /path/to/your/logs
```

### examples

**windows:**
```cmd
python imagination_insider.py C:\Users\You\Documents\my_game_logs
```

**mac:**
```bash
python imagination_insider.py ~/Documents/my_game_logs
```

**linux:**
```bash
python imagination_insider.py ~/Documents/my_game_logs
```

### it remembers your folder

the first time you run it with a folder path, it saves that. next time you can just run `python imagination_insider.py` with no path and it will use the same folder

## controls once it's running

| key | what it does |
|-----|--------------|
| j or down arrow | go to next character |
| k or up arrow | go to previous character |
| r | refresh (reload files from disk if you edited them) |
| q | quit |

## step 6: tell it who your  goons are

before you run it, you need to edit `config.py` to match your game. open it in any text editor

find the `CHARACTERS` list. it looks like this:

```python
CHARACTERS = [
    Character("zephyr", ("zephyr",)),
    Character("sunset", ("sunset",)),
    Character("jax", ("jax",)),
    # add yours here
]
```

each line is one character. the first part in quotes is the name (how it shows in the program). the second part is a list of how that character might be written in your logs. if someone is always written "Zephyr" or "zephyr", you only need one. if they're sometimes "Bob" and sometimes "Robert", you'd do:

```python
Character("bob", ("bob", "robert")),
```

add all your characters. the program counts how many times each one gets mentioned

you can also tweak `POS_WORDS` and `NEG_WORDS` (for the mood meter) and `COMBAT_WORDS` (for tension) if you want, but the default list is pretty expansive imo

## what you'll see

- **left side:** list of characters with bars showing who gets mentioned most. use j/k to pick one
- **center:** heatmap of who shows up on the same lines, plus mood, entropy, top trios and squads
- **right side:** when you select a character, you get their ties (who they appear with), keywords, and a little trend chart
- **bottom:** recent lines from your logs where the selected character appears

## troubleshooting

**"python is not recognized" or "command not found"**
- python isn't installed or isn't in your PATH. reinstall and make sure to check "Add Python to PATH" (windows) or try `python3` instead of `python`

**"no module named textual"**
- you need to run `pip install textual` (or `pip3 install textual`) from the imagination insider folder first

**"error: not a folder"**
- the path you gave doesn't exist or isn't a folder. check the path. on windows, use backslashes or quotes if there are spaces: `"C:\Users\You\My Folder\logs"`

**nothing shows up / empty dashboard**
- make sure your folder has `.txt` files in it
- make sure you edited `config.py` and added your characters
- make sure your character names/aliases match how they're written in the logs (case doesn't matter)

## what else?

do whatever you want with this! it's yours now!
