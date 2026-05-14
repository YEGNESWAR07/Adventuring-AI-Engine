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
    "  [green]n[/] [green]s[/] [green]e[/] [green]w[/]        Move in a direction\n"
    "  [green]look[/]         Examine the room around you\n"
    "  [green]inventory[/] ([green]i[/]) Show your carried items\n"
    "  [green]examine <item>[/] Describe an item in detail\n"
    "  [green]use <item>[/]    Use an item (heal, light, etc.)\n"
    "  [green]search[/]       Search for hidden items\n"
    "  [green]pickup <item>[/] Pick up an item\n"
    "  [green]drop <item>[/]   Drop an item from inventory\n"
    "  [green]attack[/]       Fight enemies in the room\n"
    "  [green]save[/]         Save your progress\n"
    "  [green]load[/]         Load saved game\n"
    "  [green]help[/]         Show this command list\n"
    "  [green]quit[/]         Exit the game\n\n"
    "[dim]Type any command above to begin your adventure...[/dim]"
)


def get_player_state(game: Game) -> dict:
    return {
        "health": game.player.health,
        "inventory": list(game.player.inventory),
        "aggressive": game.is_playing_aggressively(),
    }


def get_npc_info(npc_room: str, player_room: str) -> str:
    if npc_room == player_room:
        return f"The {NPC_NAME} is HERE with you!"
    return f"The {NPC_NAME} was last seen in {npc_room}."


def build_title() -> Panel:
    return Panel(
        Text(">> VAULT-TEC ADVENTURE TERMINAL <<", style="bold green"),
        style="bright_white on grey23",
    )


def build_stats_minimap_panel(game: Game, npc_room: str) -> Panel:
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
    if npc_room == room_name:
        npc_status = f"\n  {NPC_NAME}: [bold red]HERE[/]"
        npc_alert = " [bold red]⚠[/]"
    else:
        npc_status = f"\n  {NPC_NAME}: [cyan]{npc_room}[/]"

    mood = "AGGRESSIVE" if game.is_playing_aggressively() else "Stealth"
    mood_style = "red" if game.is_playing_aggressively() else "green"

    effects = game.get_active_effects()
    effects_line = ""
    if effects:
        effects_line = "\n" + "  ".join(effects)

    inv_count = len(game.player.inventory)
    inv_display = f"\n  Items: [bold]{inv_count}[/]"

    stats = (
        f"      HP: {hp}/100  [{hp_style}]{bar}[/]\n"
        f"    Turn: [bold]{game.turn_count}[/]\n"
        f"    Room: [bright_cyan]{room_name}[/]{npc_alert}\n"
        f"    Mood: [{mood_style}]{mood}[/]{npc_status}"
        f"{effects_line}{inv_display}"
    )

    room = game.current_room
    lines = []
    for direction, exit_data in sorted(room.exits.items()):
        dest = exit_data.room
        lock = f" [dim]🔒[{exit_data.required_item}][/]" if exit_data.required_item else ""
        lines.append(f"  {direction.upper():<6} → {dest}{lock}")
    if not lines:
        lines.append("  [dim]No exits[/]")
    minimap = "\n".join(lines)

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
    game: Game, ai_text: str, npc_room: str,
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
    layout["left"].update(build_stats_minimap_panel(game, npc_room))
    layout["center"].update(build_center_panel(ai_text, command_log, game, show_welcome, typing, show_inventory))
    layout["right"].update(build_discovery_log(discovered, npcs_met))
    layout["input_bar"].update(build_input_bar(current_input, last_command))
    return layout


def cmd_help() -> str:
    return (
        "[bold green]Commands:[/]\n"
        "[green]n/s/e/w[/]      — Move in a direction\n"
        "[green]look[/]         — Re-describe current room\n"
        "[green]inventory[/] ([green]i[/])  — Show your carried items\n"
        "[green]examine <item>[/] — Describe an item\n"
        "[green]use <item>[/]     — Use an item (heal, light, etc.)\n"
        "[green]search[/]       — Search room for hidden items\n"
        "[green]pickup <item>[/] — Pick up an item\n"
        "[green]drop <item>[/]   — Drop an item\n"
        "[green]attack[/]       — Fight enemies\n"
        "[green]save[/]         — Save game\n"
        "[green]load[/]         — Load game\n"
        "[green]help[/]         — Show this help\n"
        "[green]quit[/]         — Exit game\n"
    )
