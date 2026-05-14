import asyncio
import sys
from rich.console import Console
from rich.live import Live
from src.models import load_world, ValidationError

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from src.engine import World, Game
from src.narrator import AINarrator
from src.ui import (
    build_layout, cmd_help, get_player_state, get_npc_info,
    NPC_NAME, NPC_START, NPC_MOVE_INTERVAL,
)

console = Console()

DIR_MAP = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "north": "north", "south": "south", "east": "east", "west": "west",
    "ne": "northeast", "northeast": "northeast",
}


async def read_input_char(live, **kw):
    loop = asyncio.get_event_loop()
    text = ""
    import msvcrt

    while True:
        ch = await loop.run_in_executor(None, msvcrt.getwch)
        if ch in ('\r', '\n'):
            break
        elif ch in ('\x00', '\xe0'):
            await loop.run_in_executor(None, msvcrt.getwch)
        elif ch == '\x08':
            text = text[:-1]
        elif ch == '\x03':
            raise KeyboardInterrupt()
        else:
            text += ch
        kw['current_input'] = text
        layout = build_layout(**kw)
        live.update(layout)

    return text


async def update_display(live, **kw):
    kw['current_input'] = kw.get('current_input', '')
    layout = build_layout(**kw)
    live.update(layout)


async def main():
    try:
        world_data = load_world("data/world.json")
    except (FileNotFoundError, ValueError, ValidationError) as e:
        console.print(f"[bold red]Error loading world:[/] {e}")
        sys.exit(1)

    world = World(world_data)
    game = Game(world)
    narrator = AINarrator()

    if not game.current_room:
        console.print("[bold red]No starting room found![/]")
        sys.exit(1)

    npc_room = NPC_START
    ai_text = ""
    room_just_changed = True
    discovered_items = set()
    encountered_npcs = set()
    command_log = []
    show_welcome = True
    typing = False
    show_inventory = False
    npc_just_entered = False
    last_command = ""
    current_input = ""
    turns_in_same_room = 0
    last_room_name = game.current_room.name
    hint_countdown = 0

    def build_kw(**overrides):
        kwargs = dict(
            game=game, ai_text=ai_text, npc_room=npc_room,
            discovered=discovered_items, npcs_met=encountered_npcs,
            command_log=command_log, show_welcome=show_welcome,
            typing=typing, show_inventory=show_inventory,
            last_command=last_command, current_input=current_input,
        )
        kwargs.update(overrides)
        return kwargs

    layout = build_layout(**build_kw())
    try:
        with Live(layout, refresh_per_second=4, screen=True) as live:
            await asyncio.sleep(0.5)

            while not game.game_over:
                if room_just_changed:
                    typing = True
                    await update_display(live, **build_kw(typing=True))

                    ai_text = await narrator.generate_room_desc(
                        game.current_room.to_dict(),
                        get_player_state(game),
                        recent_actions=list(game.recent_actions),
                        npc_info=get_npc_info(npc_room, game.current_room.name),
                    )
                    typing = False
                    for enemy in game.current_room.enemies:
                        encountered_npcs.add(enemy)
                    room_items = game.current_room.items
                    if room_items:
                        command_log.append(f"[green]Items here:[/] {', '.join(f'[yellow]{i}[/]' for i in room_items)}")
                    if game.current_room.enemies:
                        command_log.append(f"[red]Lurking:[/] {', '.join(f'[bold red]{e}[/]' for e in game.current_room.enemies)}")
                    room_just_changed = False
                    turns_in_same_room = 0
                    hint_countdown = 5

                if npc_just_entered:
                    npc_desc = await narrator.generate_npc_encounter(
                        NPC_NAME, game.current_room.name, get_player_state(game),
                    )
                    if npc_desc:
                        command_log.append(f"[bold red]▸ {npc_desc}[/]")
                    else:
                        command_log.append(f"[bold red]▸ {NPC_NAME} slinks into the room![/]")
                    npc_just_entered = False

                game.tick_effects()

                await update_display(live, **build_kw())

                try:
                    raw = await read_input_char(live, **build_kw())
                except (asyncio.CancelledError, KeyboardInterrupt):
                    command_log.append("[red]Game interrupted.[/]")
                    game.game_over = True
                    break

                cmd = raw.strip().lower()
                if not cmd:
                    continue

                command_log.append(f"> [bold white]{cmd}[/]")
                game.turn_count += 1
                show_inventory = False
                last_command = cmd
                current_input = ""

                if show_welcome:
                    show_welcome = False

                if game.current_room.name == last_room_name:
                    turns_in_same_room += 1
                else:
                    turns_in_same_room = 0
                    hint_countdown = 5
                last_room_name = game.current_room.name

                hint_countdown -= 1
                if hint_countdown <= 0 and turns_in_same_room >= 3 and narrator.client:
                    hint = await narrator.generate_hint(
                        game.current_room.to_dict(), get_player_state(game), turns_in_same_room,
                    )
                    if hint:
                        command_log.append(f"[dim italic]{{A voice whispers:}}[/] [italic]{hint}[/]")
                    hint_countdown = 5

                if cmd in ("quit", "exit"):
                    command_log.append("[red]Thanks for playing![/]")
                    break

                elif cmd == "help":
                    command_log.append(cmd_help())

                elif cmd in ("inventory", "i"):
                    show_inventory = True
                    command_log.append("[green]▸ Opening inventory...[/]")

                elif cmd == "search":
                    result = game.search_room()
                    command_log.append(result)
                    game.add_action("searched room")

                elif cmd.startswith("examine ") or cmd.startswith("exam "):
                    item = cmd[9:] if cmd.startswith("examine ") else cmd[5:]
                    lore = game.examine_item(item)
                    if narrator.client and item in game.player.inventory:
                        ai_lore = await narrator.generate_item_description(
                            item, context=f"The player is in {game.current_room.name}.",
                        )
                        if ai_lore:
                            lore += f"\n  [dim]{{The narrator adds:}}[/] [italic]{ai_lore}[/]"
                    command_log.append(lore)
                    game.add_action(f"examined {item}")

                elif cmd.startswith("use "):
                    item = cmd[4:]
                    result = game.use_item(item)
                    command_log.append(result)

                elif cmd in DIR_MAP:
                    direction = DIR_MAP[cmd]
                    moved = game.move(direction)
                    game.add_action(f"moved {direction}")
                    if moved:
                        command_log.append(f"[green]▸ You move {direction}...[/]")
                        room_just_changed = True
                        show_inventory = False
                        if npc_room == game.current_room.name:
                            npc_just_entered = True
                    else:
                        info = game.current_room.exits.get(direction)
                        if info and info.required_item:
                            command_log.append(f"[yellow]▸ Need '[bold]{info.required_item}[/]' to go that way.[/]")
                        else:
                            command_log.append("[red]▸ Can't go that way.[/]")

                elif cmd == "look":
                    room_data = game.current_room.to_dict()
                    ai_text = room_data.get("static_description") or room_data.get("description", "A dark room.")
                    room = game.current_room
                    parts = ["[green]▸ You look around...[/]"]
                    if room.items:
                        parts.append(f"[green]Items visible:[/] {', '.join(f'[yellow]{i}[/]' for i in room.items)}")
                    if room.enemies:
                        parts.append(f"[red]Enemies:[/] {', '.join(f'[bold red]{e}[/]' for e in room.enemies)}")
                    command_log.append("\n".join(parts))

                elif cmd.startswith("pickup ") or cmd.startswith("pick "):
                    item = cmd[7:] if cmd.startswith("pickup ") else cmd[5:]
                    game.pick_up_item(item)
                    game.add_action(f"picked {item}")
                    if item in game.player.inventory:
                        discovered_items.add(item)
                        command_log.append(f"[green]▸ Picked up [yellow]{item}[/].[/]")
                    else:
                        command_log.append(f"[red]▸ {item} is not here.[/]")

                elif cmd.startswith("drop "):
                    item = cmd[5:]
                    game.drop_item(item)
                    game.add_action(f"dropped {item}")
                    if item not in game.player.inventory:
                        command_log.append(f"[green]▸ Dropped [yellow]{item}[/].[/]")
                    else:
                        command_log.append(f"[red]▸ You don't have {item}.[/]")

                elif cmd in ("attack", "fight"):
                    for enemy in game.current_room.enemies:
                        encountered_npcs.add(enemy)
                    result = game.combat_round()
                    command_log.append(f"{result}")
                    if game.game_over:
                        break

                elif cmd == "save":
                    game.save_game()
                    game.add_action("saved game")
                    command_log.append("[green]▸ Game saved![/]")

                elif cmd == "load":
                    game.load_game("savegame.json")
                    game.add_action("loaded game")
                    room_just_changed = True
                    command_log.append("[green]▸ Game loaded![/]")

                else:
                    command_log.append(f"[red]▸ Unknown command: '{cmd}'. Type 'help' for commands.[/]")

                npc_was_in_room = npc_room == game.current_room.name
                if game.turn_count % NPC_MOVE_INTERVAL == 0:
                    npc_room_obj = world.get_room(npc_room)
                    if npc_room_obj:
                        exits = list(npc_room_obj.exits.keys())
                        if exits:
                            chosen = await narrator.move_npc(
                                NPC_NAME, npc_room, exits,
                                context=f"The player is in {game.current_room.name}. ",
                            )
                            next_room = npc_room_obj.get_exit_room(chosen)
                            if next_room and world.get_room(next_room):
                                npc_room = next_room
                                game.add_action(f"{NPC_NAME} moved to {npc_room}")
                                if npc_room == game.current_room.name and not npc_was_in_room:
                                    npc_just_entered = True

                if game.current_room.name == "Sunlit Valley":
                    game.game_over = True
                    command_log.append("[bold green]██  YOU ESCAPE THE DARKNESS!  ██[/]")
                    command_log.append("[bold yellow]Adventure Complete! Congratulations![/]")

            await update_display(live, **build_kw())
            await asyncio.sleep(1.5)

        console.print()
        if game.current_room.name == "Sunlit Valley":
            console.print("[bold green]██ You have escaped the dungeon! ██[/]")
            console.print("[bold yellow]Congratulations, adventurer![/]")
            console.print("[green]You survived [bold]{}[/] turns and collected [bold]{}[/] items.[/]".format(
                game.turn_count, len(discovered_items)))
        elif game.game_over:
            console.print("[bold red]*** YOU HAVE DIED ***[/]")
            console.print("[bold]Your journey ends here...[/]")
            console.print("[red]You lasted [bold]{}[/] turns.[/]".format(game.turn_count))
        console.print()
    except (asyncio.CancelledError, KeyboardInterrupt):
        console.print("\n[bold yellow]Game terminated by user.[/]")


if __name__ == "__main__":
    asyncio.run(main())
