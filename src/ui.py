from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from src.engine import Game

NPC_NAME = "Shadow Thief"
NPC_START = "Goblin Cavern"
NPC_MOVE_INTERVAL = 5

WELCOME_TEXT = (
    "[bold yellow]╔══════════════════════════════╗[/]\n"
    "[bold yellow]║      WELCOME, ADVENTURER!    ║[/]\n"
    "[bold yellow]╚══════════════════════════════╝[/]\n\n"
    "[bold]Available Commands:[/]\n"
    "  [green]n[/] [green]s[/] [green]e[/] [green]w[/] [green]ne[/] [green]nw[/]    Move\n"
    "  [green]look[/]           Examine the room\n"
    "  [green]inventory[/] ([green]i[/])   Show carried items\n"
    "  [green]examine <item>[/]  Describe an item\n"
    "  [green]use <item>[/]      Use an item\n"
    "  [green]equip <item>[/]    Equip weapon/armor/accessory\n"
    "  [green]search[/]         Search for hidden items\n"
    "  [green]talk <npc>[/]     Talk to a character\n"
    "  [green]wares[/]          See merchant's inventory\n"
    "  [green]trade <give> <get>[/] Trade with merchant\n"
    "  [green]codex <query>[/]  Search the lore database\n"
    "  [green]pickup <item>[/]   Pick up an item\n"
    "  [green]drop <item>[/]     Drop an item\n"
    "  [green]attack[/]         Fight enemies\n"
    "  [green]save[/]           Save progress\n"
    "  [green]load[/]           Load game\n"
    "  [green]help[/]           Show this list\n"
    "  [green]quit[/]           Exit\n\n"
    "[dim]Type any command above to begin your adventure...[/dim]"
)


def get_player_state(game: Game) -> dict:
    return {
        "health": game.player.health,
        "inventory": list(game.player.inventory),
        "aggressive": game.is_playing_aggressively(),
    }


def get_npc_info(game: Game, player_room: str) -> str:
    here = [n for n in game.npcs.values() if n.current_room == player_room and n.role != "merchant"]
    if here:
        names = ", ".join(n.name for n in here)
        return f"{names} {'are' if len(here) > 1 else 'is'} here with you."
    nearby = [n for n in game.npcs.values() if n.role != "merchant"]
    if nearby:
        rooms = set(n.current_room for n in nearby)
        return f"You sense presences in: {', '.join(sorted(rooms)[:2])}."
    return "You feel alone in the darkness."


def build_title() -> Panel:
    return Panel(
        Text(">> VAULT-TEC ADVENTURE TERMINAL <<", style="bold green"),
        style="bright_white on grey23",
    )


def generate_ascii_minimap(game: Game) -> str:
    room = game.current_room
    if not room:
        return "  [dim]No Map Available[/]"
        
    # Get exits
    n_room = room.get_exit_room("north")
    s_room = room.get_exit_room("south")
    e_room = room.get_exit_room("east")
    w_room = room.get_exit_room("west")
    
    # Helper to truncate and format room name
    def fmt_room(name: Optional[str]) -> str:
        if not name:
            return ""
        # Let's keep it compact, e.g. 10 chars max
        if len(name) > 10:
            return f"[{name[:8]}..]"
        return f"[{name}]"

    n_str = fmt_room(n_room)
    s_str = fmt_room(s_room)
    e_str = fmt_room(e_room)
    w_str = fmt_room(w_room)

    # Rich formatted center marker
    current_str = "[bold green]●[/]"
    
    lines = []
    
    # Line 1: North Room
    if n_room:
        lines.append(f"{n_str:^28}")
        lines.append(f"{'▲':^28}")
        lines.append(f"{'│':^28}")
        
    # Line 2: West Room <--- Center ---> East Room
    w_part = f"{w_str} ◄───" if w_room else " " * 11
    e_part = f"───► {e_str}" if e_room else ""
    
    # Measure visual length excluding formatting
    len_w = len(w_str) + 5 if w_room else 11
    len_e = len(e_str) + 5 if e_room else 0
    total_len = len_w + 1 + len_e
    
    left_padding = (28 - total_len) // 2
    if left_padding < 0:
        left_padding = 0
        
    center_line = " " * left_padding + (f"{w_str} ◄───" if w_room else " " * 11) + current_str + (f"───► {e_str}" if e_room else "")
    lines.append(center_line)
    
    # Line 3: South Room
    if s_room:
        lines.append(f"{'│':^28}")
        lines.append(f"{'▼':^28}")
        lines.append(f"{s_str:^28}")
        
    # Diagonal exits and others
    other_exits = []
    for direction, exit_data in sorted(room.exits.items()):
        if direction not in ["north", "south", "east", "west"]:
            lock = " 🔒" if exit_data.required_item else ""
            other_exits.append(f"  {direction.upper():<4} → {exit_data.room}{lock}")
            
    # Include locks for N, S, E, W exits
    locks = []
    for direction, exit_data in sorted(room.exits.items()):
        if direction in ["north", "south", "east", "west"] and exit_data.required_item:
            locks.append(f"  {direction.upper()} 🔒 requires {exit_data.required_item}")
            
    map_str = "\n".join(lines)
    
    extras = []
    if other_exits:
        extras.extend(other_exits)
    if locks:
        extras.extend(locks)
        
    if extras:
        map_str += "\n\n" + "\n".join(extras)
        
    return map_str


def build_stats_minimap_panel(game: Game) -> Panel:
    from typing import Optional
    hp = game.player.health
    filled = "█" * (hp // 5)
    empty = "░" * ((100 - hp) // 5)
    bar = f"{filled}{empty}"
    if hp > 50:
        hp_style = "bold green"
        border = "cyan"
    elif hp > 25:
        hp_style = "bold yellow"
        border = "yellow"
    else:
        hp_style = "bold red blink"
        border = "red"

    room_name = game.current_room.name
    npc_status = ""
    npc_alert = ""
    room_npcs = game.get_npcs_in_room(room_name)

    for n in room_npcs:
        role_colors = {"merchant": "green", "oracle": "magenta", "trickster": "red", "guide": "cyan", "guardian": "yellow", "bard": "blue"}
        col = role_colors.get(n.role, "white")
        npc_status += f"\n  [{col}]◆ {n.name}[/]"

    mood = "AGGRESSIVE" if game.is_playing_aggressively() else "Stealth"
    mood_style = "red" if game.is_playing_aggressively() else "green"

    effects = game.get_active_effects()
    effects_line = ""
    if effects:
        effects_line = "\n" + "  ".join(effects)

    inv_count = len(game.player.inventory)
    eq = game.player.equipment
    eq_text = f"  ATK:{game.player.attack_bonus} DEF:{game.player.defense_bonus}"
    if eq["weapon"]:
        eq_text += f" ⚔{eq['weapon']}"
    if eq["armor"]:
        eq_text += f" 🛡{eq['armor']}"

    stats = (
        f"      HP: {hp}/{game.player.max_hp}  [{hp_style}]{bar}[/]\n"
        f"    Turn: [bold]{game.turn_count}[/]\n"
        f"    Room: [bright_cyan]{room_name}[/]{npc_alert}\n"
        f"    Mood: [{mood_style}]{mood}[/]{eq_text}"
        f"{effects_line}\n  Items: [bold]{inv_count}[/]{npc_status}"
    )

    minimap = generate_ascii_minimap(game)

    text = f"{stats}\n\n[bold]MINI-MAP[/]\n{minimap}"
    return Panel(text, title="[bold]PLAYER STATS[/]", border_style=border)


def build_inventory_content(game: Game) -> str:
    inv = game.player.inventory
    if not inv:
        return "[dim]Your inventory is empty.[/]"

    lines = ["[bold]Carried Items:[/]"]
    for i, item in enumerate(sorted(inv), 1):
        lines.append(f"  {i}. [yellow]{item}[/]")
    lines.append(f"\n[dim]Total: {len(inv)} item{'s' if len(inv) != 1 else ''}[/]")
    return "\n".join(lines)


def build_center_panel(ai_text: str, command_log: list, game: Game, show_welcome: bool = False, typing: bool = False, show_inventory: bool = False) -> Panel:
    if show_welcome:
        title = "[bold]STORY FEED[/]"
        content = WELCOME_TEXT
    elif show_inventory:
        title = "[bold yellow]INVENTORY[/]"
        content = build_inventory_content(game)
    elif typing:
        title = "[bold]STORY FEED[/]"
        content = "[yellow]✦ The narrator is weaving the story...[/]"
    else:
        title = "[bold]STORY FEED[/]"
        parts = [ai_text]

        room = game.current_room
        if room.items:
            items_str = ", ".join(f"[yellow]{item}[/]" for item in room.items)
            parts.append(f"\n[bold]Items here:[/] {items_str}")
        if room.enemies:
            enemies_str = ", ".join(f"[bold red]{enemy}[/]" for enemy in room.enemies)
            parts.append(f"[bold]Enemies:[/] {enemies_str}")

        if game.get_active_effects():
            effects_str = " | ".join(game.get_active_effects())
            parts.append(f"\n[bold]Effects:[/] {effects_str}")

        if command_log:
            parts.append("")
            parts.append("[bold]Recent:[/]")
            for entry in command_log[-6:]:
                parts.append(f"  {entry}")
        content = "\n".join(parts)

    border = "bright_blue"
    if game.player.health <= 25:
        border = "red"
    elif game.player.health <= 50:
        border = "yellow"

    return Panel(content, title=title, border_style=border, padding=(1, 2))


def build_discovery_log(discovered: set, npcs_met: set) -> Panel:
    items_text = ""
    if discovered:
        for item in sorted(discovered):
            items_text += f"\n  ◆ [yellow]{item}[/]"
    else:
        items_text = "\n  [dim]None yet[/]"

    npcs_text = ""
    if npcs_met:
        for npc in sorted(npcs_met):
            npcs_text += f"\n  ◇ [magenta]{npc}[/]"
    else:
        npcs_text = "\n  [dim]None yet[/]"

    text = f"[bold]ITEMS FOUND[/]{items_text}\n\n[bold]NPCs MET[/]{npcs_text}"
    return Panel(text, border_style="yellow")


def build_input_bar(current_input: str = "", last_command: str = "") -> Panel:
    if current_input:
        content = f"[bold cyan]>[/] [bold white]{current_input}[/][reverse] [/]"
    elif last_command:
        content = f"[bold cyan]>[/] [dim]{last_command}[/]"
    else:
        content = "[bold cyan]>[/] [dim]Type a command...[/dim]"
    return Panel(content, style="on grey23", height=3)


def build_layout(
    game: Game, ai_text: str,
    discovered: set, npcs_met: set, command_log: list,
    show_welcome: bool = False, typing: bool = False,
    show_inventory: bool = False, last_command: str = "",
    current_input: str = "",
) -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="input_bar", size=3),
    )
    layout["header"].update(build_title())
    layout["body"].split_row(
        Layout(name="left", ratio=20),
        Layout(name="center", ratio=60),
        Layout(name="right", ratio=20),
    )
    layout["left"].update(build_stats_minimap_panel(game))
    layout["center"].update(build_center_panel(ai_text, command_log, game, show_welcome, typing, show_inventory))
    layout["right"].update(build_discovery_log(discovered, npcs_met))
    layout["input_bar"].update(build_input_bar(current_input, last_command))
    return layout


def cmd_help() -> str:
    return (
        "[bold green]Commands:[/]\n"
        "[green]n/s/e/w/ne/nw/up/down[/]  — Move\n"
        "[green]look[/]           — Examine room\n"
        "[green]inventory[/] ([green]i[/])    — Show carried items\n"
        "[green]examine <item>[/]  — Describe an item\n"
        "[green]use <item>[/]      — Use an item\n"
        "[green]equip <item>[/]    — Equip weapon/armor/accessory\n"
        "[green]search[/]         — Search for hidden items\n"
        "[green]talk <npc>[/]     — Talk to a character\n"
        "[green]wares[/]          — See merchant's wares\n"
        "[green]trade <give> <get>[/]  — Trade with merchant\n"
        "[green]codex <query>[/]  — Search the lore database\n"
        "[green]pickup <item>[/]  — Pick up an item\n"
        "[green]drop <item>[/]    — Drop an item\n"
        "[green]attack[/]        — Fight enemies\n"
        "[green]save[/]          — Save game\n"
        "[green]load[/]          — Load game\n"
        "[green]help[/]          — Show this help\n"
        "[green]quit[/]          — Exit game\n"
    )
