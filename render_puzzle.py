"""This file was vibe-coded with Gemini 3.0 in Antigravity, because UIs are not my jam."""

import argparse
import math
from typing import Mapping
import sys

from clockchecker.core import Puzzle, Player
from clockchecker import characters, info, events

# Mapping of character class names to their script folders on the official assets site
TB_CHARACTERS = {
    "Washerwoman", "Librarian", "Investigator", "Chef", "Empath",
    "FortuneTeller", "Undertaker", "Monk", "Ravenkeeper", "Slayer",
    "Soldier", "Mayor", "Butler", "Drunk", "Recluse", "Saint",
    "Imp", "Baron", "Poisoner", "Spy", "ScarletWoman",
}
BMR_CHARACTERS = {
    "Grandmother", "Sailor", "Chambermaid", "Exorcist", "Innkeeper",
    "Gambler", "Gossip", "Courtier", "Professor", "Minstrel",
    "TeaLady", "Pacifist", "Fool", "Tinker", "Moonchild",
    "Goon", "Lunatic", "Godfather", "DevilsAdvocate", "Assassin",
    "Mastermind", "Zombuul", "Pukka", "Shabaloth", "Po",
}
SNV_CHARACTERS = {
    "Clockmaker", "Dreamer", "SnakeCharmer", "Mathematician", "Flowergirl",
    "TownCrier", "Oracle", "Savant", "Artist", "Philosopher",
    "Sage", "Mutant", "Sweetheart", "Klutz", "EvilTwin",
    "Witch", "Cerenovus", "PitHag", "FangGu", "Vortox",
    "NoDashii", "Lleech", "Vigormortis", "Juggler", "Seamstress",
}

def get_character_script(name: str) -> str:
    if name in TB_CHARACTERS:
        return 'tb'
    if name in BMR_CHARACTERS:
        return 'bmr'
    if name in SNV_CHARACTERS:
        return 'snv'
    return "carousel"

def get_icon_url(character_type: type, is_evil: bool) -> str:
    name = character_type.__name__
    script = get_character_script(name)
    alignment = "e" if is_evil or issubclass(character_type, (characters.Minion, characters.Demon)) else "g"
    asset_name = name.lower().replace(" ", "").replace("_", "")
    return f"https://script.bloodontheclocktower.com/src/assets/icons/{script}/{asset_name}_{alignment}.webp"

def render_puzzle(puzzle: Puzzle) -> str:
    """
    Produces a standalone HTML visualization of a Puzzle object.
    Final spacing and background consistency fix.
    """
    n_players = len(puzzle.players)
    names = {i: p.name for i, p in enumerate(puzzle.players)}
    names = [p.name for p in puzzle.players]
    
    player_html = []
    token_radius = max(20, n_players * 3.1)
    info_radius = token_radius + 9.5
    
    player_deaths = {}
    max_night_val = max(list(puzzle.night_deaths.keys()) + list(puzzle.day_events.keys()) + [0])
    
    for n in range(1, max_night_val + 1):
        if n in puzzle.night_deaths:
            deaths = puzzle.night_deaths[n]
            if isinstance(deaths, (int, events.Event)): deaths = [deaths]
            for death in deaths:
                pid = death.player if hasattr(death, 'player') else death
                if pid not in player_deaths:
                    player_deaths[pid] = {"text": f"Died N{n}", "type": "nature"}
        
        if n in puzzle.day_events:
            evs = puzzle.day_events[n]
            if not isinstance(evs, list): evs = [evs]
            for ev in evs:
                if isinstance(ev, events.Execution) and ev.died:
                    if ev.player not in player_deaths:
                        player_deaths[ev.player] = {"text": f"Executed D{n}", "type": "execution"}
                elif hasattr(ev, 'died') and ev.died and hasattr(ev, 'player'):
                    if ev.player not in player_deaths:
                        player_deaths[ev.player] = {"text": f"Died D{n}", "type": "nature"}

    for i, player in enumerate(puzzle.players):
        angle_deg = (i * 360 / n_players) - 90
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        token_left = 50 + token_radius * cos_a
        token_top = 50 + token_radius * sin_a
        info_left = 50 + info_radius * cos_a
        info_top = 50 + info_radius * sin_a
        
        is_evil = player.is_evil or issubclass(player.claim, (characters.Minion, characters.Demon))
        color_class = "townsfolk"
        if issubclass(player.claim, characters.Demon):
            color_class = "demon"
        elif issubclass(player.claim, characters.Minion):
            color_class = "minion"
        elif issubclass(player.claim, characters.Outsider):
            color_class = "outsider"
            
        death_info = player_deaths.get(i)
        dead_class = "dead" if death_info else ""
        death_type_class = death_info["type"] if death_info else ""
        death_label = death_info["text"] if death_info else ""
        
        icon_url = get_icon_url(player.claim, is_evil)
        
        player_info_lines = []
        for (night, char), item in puzzle._night_info[i].items():
            info_str = item.display(names).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            player_info_lines.append(f"<strong>N{night}:</strong> {info_str}")
        for (day, char), item in puzzle._day_info[i].items():
            info_str = item.display(names).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            player_info_lines.append(f"<strong>D{day}:</strong> {info_str}")
        info_html = "<br>".join(player_info_lines)
        
        tx = "0"; ty = "0"; info_text_align = "center"
        if cos_a > 0.4: 
            tx = "0%"
            info_text_align = "left"
            ty = "-50%"
            info_max_width = "180px"
        elif cos_a < -0.4: 
            # Left side: anchor to right edge so it stays close to token
            tx = "-100%"
            info_text_align = "right"
            ty = "-50%"
            info_max_width = "180px"
        else: 
            tx = "-50%"
            info_text_align = "center"
            if sin_a < 0: ty = "-100%"
            else: ty = "0%"
            info_max_width = "350px"

        info_box_html = f"""
            <div class="player-info-outer" style="left: {info_left}%; top: {info_top}%; transform: translate({tx}, {ty}); text-align: {info_text_align};">
                <div class="player-info-content" style="max-width: {info_max_width};">{info_html}</div>
            </div>
            """ if info_html else ""

        player_html.append(f"""
            <div class="player-token-container" style="left: {token_left}%; top: {token_top}%;">
                <div class="player-token {color_class} {dead_class} {death_type_class}" data-death="{death_label}">
                    <div class="token-icon-wrap">
                        <img src="{icon_url}" class="role-icon" onerror="this.src='https://wiki.bloodontheclocktower.com/images/1/1a/Icon_townsfolk.png'">
                    </div>
                    <div class="role-name">{player.claim.__name__}</div>
                </div>
                <div class="player-name-label">{player.name}</div>
            </div>
            {info_box_html}
        """)
    
    unique_hidden = []
    all_hidden = puzzle.demons + puzzle.minions + puzzle.hidden_good + puzzle.hidden_self
    for h in all_hidden:
        if h not in unique_hidden:
            unique_hidden.append(h)
            
    hidden_html_items = []
    for role in unique_hidden:
        h_is_evil = issubclass(role, (characters.Minion, characters.Demon))
        h_icon = get_icon_url(role, h_is_evil)
        hidden_html_items.append(f"""
            <div class="hidden-role-token">
                <div class="token-icon-wrap" style="width: 55px; height: 55px; border: 2px solid var(--accent); position: relative;">
                    <img src="{h_icon}" class="role-icon" style="width: 100%; height: 100%; object-fit: contain; transform: scale(1.3);">
                </div>
                <div class="hidden-role-name">{role.__name__}</div>
            </div>
        """)

    event_html = []
    for n in range(1, max_night_val + 1):
        # Night n deaths
        if n in puzzle.night_deaths:
            deaths = puzzle.night_deaths[n]
            if not isinstance(deaths, list):
                deaths = [deaths]
            for d in deaths:
                if hasattr(d, 'display'):
                    d_str = d.display(names)
                else:
                    # Fallback for raw PlayerIDs
                    d_str = f"{names[d]} dies"
                event_html.append(f"<div><strong class='event-label'>N{n}:</strong> {d_str}</div>")
        
        # Day n events
        if n in puzzle.day_events:
            evs = puzzle.day_events[n]
            if not isinstance(evs, list):
                evs = [evs]
            for ev in evs:
                ev_str = ev.display(names).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                event_html.append(f"<div><strong class='event-label'>D{n}:</strong> {ev_str}</div>")
    
    events_section = f'<div class="events-box">{"".join(event_html)}</div>' if event_html else ""

    html = f"""
    <div class="puzzle-app-container">
        <div class="puzzle-scaler">
            <div class="puzzle-window">
                {events_section}
                {"".join(player_html)}
            </div>
            
            <div class="hidden-roles-container">
                <div class="hidden-roles-title">Potential hidden roles:</div>
                <div class="hidden-roles-list">
                    {"".join(hidden_html_items)}
                </div>
            </div>
        </div>
    </div>
    """
    return html

def make_standalone_page(puzzles: Puzzle | list[Puzzle]) ->str:
    if isinstance(puzzles, Puzzle):
        puzzles = [puzzles]
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ClockChecker Puzzle Visualisation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #1b2631;
            --accent: #1abc9c;
            --text-white: #ffffff;
            --border: #2e4053;
            --puzzle-target-width: 750px;
            --puzzle-internal-width: 1000px;
            --puzzle-scale: calc(var(--puzzle-target-width) / var(--puzzle-internal-width));
        }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-white);
            font-family: 'Inter', sans-serif;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .puzzle-app-container {{
            width: var(--puzzle-target-width);
            /* Scaling factor affects the displayed height, so we use a wrapper hack or just let it flow */
            overflow: visible;
        }}
        .puzzle-scaler {{
            width: var(--puzzle-internal-width);
            transform: scale(var(--puzzle-scale));
            transform-origin: top left;
        }}
        .puzzle-window {{
            position: relative;
            width: 1000px;
            height: 900px;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            user-select: none;
        }}
        .player-token-container {{
            position: absolute;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            z-index: 10;
        }}
        .player-token {{
            width: 130px;
            height: 130px;
            border-radius: 50%;
            background-color: #fffdf5;
            border: 3px solid #555;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            position: relative;
            overflow: visible;
        }}
        .token-icon-wrap {{
            width: 80%;
            height: 80%;
            border-radius: 50%;
            overflow: hidden;
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #fffdf5; /* Restored background */
        }}
        .role-icon {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            transform: scale(1.3);
            margin-top: -10%;
        }}
        .role-name {{
            font-size: 13px;
            font-weight: bold;
            color: #333;
            text-shadow: 0 0 2px white;
            text-align: center;
            position: absolute;
            bottom: 12%;
            z-index: 8;
            width: 100%;
        }}
        .player-name-label {{
            margin-top: 8px;
            font-size: 20px;
            font-weight: 500;
            color: var(--accent);
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }}
        
        .player-info-outer {{
            position: absolute;
            z-index: 5;
            pointer-events: none;
        }}
        .player-info-content {{
            font-size: 14px;
            color: var(--text-white);
            line-height: 1.4;
            background: rgba(0, 0, 0, 0.45);
            padding: 8px;
            border-radius: 8px;
            border-left: 3px solid var(--accent);
            width: fit-content;
        }}
        
        .player-token.townsfolk {{ border-color: #1a73e8; }}
        .player-token.outsider {{ border-color: #1a73e8; opacity: 0.95; }}
        .player-token.minion {{ border-color: #d93025; }}
        .player-token.demon {{ border-color: #a50e0e; box-shadow: 0 0 20px rgba(165, 14, 14, 0.6); }}
        
        .player-token.dead::before {{
            content: "";
            position: absolute;
            width: 90px;
            height: 140px;
            top: -5px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 2;
            opacity: 0.7;
            clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 50% 85%, 0% 100%);
            border: 1px solid rgba(0,0,0,0.3);
        }}
        .player-token.dead.nature::before {{ background-color: #c62828; border-top: 2px solid #500; }}
        .player-token.dead.execution::before {{ background-color: #1565c0; border-top: 2px solid #003; }}
        
        .player-token.dead::after {{
             content: attr(data-death);
             position: absolute;
             z-index: 6;
             top: 5px;
             left: 0;
             right: 0;
             color: white;
             font-weight: bold;
             font-size: 14px;
             text-shadow: 1px 1px 2px rgba(0,0,0,0.9);
             text-align: center;
        }}
        
        .events-box {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            border-radius: 10px;
            width: fit-content;
            max-width: 250px;
            text-align: center;
            font-size: 14px;
            background: rgba(0, 0, 0, 0.45);
            padding: 10px;
            z-index: 1;
            color: var(--text-white);
            backdrop-filter: blur(5px);
        }}
        .event-label {{
            color: var(--accent);
            opacity: 0.8;
        }}
        
        .hidden-roles-container {{
            border: 2px solid var(--border);
            padding: 10px 15px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 30px;
            background: rgba(46, 64, 83, 0.3);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: fit-content;
            margin: 20px auto 0 auto;
        }}
        .hidden-roles-title {{
            font-size: 16px;
            color: var(--accent);
            font-weight: bold;
            white-space: nowrap;
            letter-spacing: 1px;
        }}
        .hidden-roles-list {{
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
            justify-content: flex-start;
        }}
        .hidden-role-token {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            width: 70px;
            overflow: visible;
        }}
        .hidden-role-name {{
            font-size: 12px;
            color: var(--accent);
            font-weight: 600;
            text-align: center;
        }}
    </style>
</head>
<body>
{"".join(render_puzzle(p) for p in puzzles)}
</body>
</html>
"""

if __name__ == "__main__":
    import puzzles

    PREFIXES = ('puzzle_', '_puzzle_')
    puzzle_names = [
        full_name[len(prefix):]
        for full_name in dir(puzzles) for prefix in PREFIXES
        if full_name.startswith(prefix)
    ]
    parser = argparse.ArgumentParser()
    parser.add_argument('puzzle_name', choices=puzzle_names, nargs='?', default='1')
    args = parser.parse_args(sys.argv[1:])

    for prefix in PREFIXES:
        factory = getattr(puzzles, f'{prefix}{args.puzzle_name}', None)
        if factory is not None:
            puzzle_def = factory()
            html = make_standalone_page(puzzle_def.puzzle)
            filename = f"testvis.html"
            with open(filename, "w") as f:
                f.write(html)
            print(f"Generated {filename}")
        break
    else:
        raise ValueError(f"Puzzle {args.puzzle_name} not found")