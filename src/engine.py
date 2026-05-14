import json
import random
from typing import Dict, List, Optional, Callable
from collections import deque
from src.models import WorldData, RoomData


ITEM_LORE = {
    "torch": "A simple wooden torch wrapped in oil-soaked cloth. It will light your way through the darkness.",
    "map": "A faded parchment map of the cave system. Several paths are marked in faded ink, including one that leads to sunlight.",
    "rusty key": "A heavily corroded iron key. The teeth are still intact despite the rust. It probably fits an old lock somewhere.",
    "ancient coin": "A gold coin from a forgotten era. One side bears a crowned skull, the other a coiled serpent.",
    "golden idol": "A fist-sized idol of pure gold, shaped like a crouching beast with emerald eyes that gleam in the dark.",
    "legendary blade": "A sword that hums with latent power. The blade is etched with ancient runes that pulse with a faint blue light.",
    "healing salve": "A clay pot filled with a fragrant green ointment. It smells of mountain herbs and faint magic.",
    "shield": "A sturdy iron shield bearing the crest of a long-dead knightly order. It could block a heavy blow.",
    "iron helm": "A battle-worn iron helm. The inside is padded with decayed leather. It offers some protection.",
    "diamond ring": "A brilliant diamond ring set in silver. It catches the light even in the deepest darkness.",
    "ruby": "A blood-red ruby the size of your thumb. It pulses with a warm, rhythmic inner light.",
    "rusty sword": "A sword recovered from the lakebed. It is pitted with rust but the edge is still dangerously sharp.",
    "ancient scroll": "A brittle scroll covered in ornate script. The language is ancient and unfamiliar to you.",
    "crystal focus": "A clear crystal sphere that hums with contained energy. It feels warm and alive to the touch.",
    "dragon heart": "The still-warm heart of an elder wyrm. It radiates immense primal power.",
    "gem of power": "A faceted gem that glows with captured starlight. You feel stronger just holding it.",
    "gold coin": "A single gold coin. It feels warm, as if newly minted — but that is impossible in this place.",
    "ancient crown": "A crown of black iron and silver, set with stones that gleam like captured moonlight.",
    "goblin tooth": "A sharp yellowed tooth from a goblin. It might be worth something to a collector.",
    "silver chalice": "An ornate silver chalice etched with vines and lunar phases. It feels sacred.",
    "chainmail fragment": "A fragment of chainmail from a forgotten soldier. The rings are still strong.",
    "waterlogged scroll": "A scroll that has been underwater for years. Most of the ink has run, but you can make out a map fragment.",
    "rat whisker": "A long, twitchy whisker from a giant rat. It still has some spring to it.",
    "ancient talisman": "A stone talisman carved with protective runes. It hums faintly against your skin.",
    "dragon scale": "A single scale from an elder wyrm. It's hot to the touch and shimmering with iridescent color.",
    "small key": "A small brass key. It looks like it might open a chest or a lockbox.",
    "health potion": "A glass vial filled with crimson liquid that glows with a soft inner light. It radiates warmth and vitality.",
    "greater health potion": "A larger vial of deep ruby liquid. The healing essence inside swirls like liquid fire. It feels immensely powerful.",
    "elven bread": "A small loaf of sweet elven bread wrapped in leaves. It smells of honey and wildflowers. Eating it restores energy.",
    "bandages": "A roll of clean linen bandages. They can be used to bind wounds and stop bleeding.",
    "mysterious herb": "A dried herb with silver veins running through its leaves. It pulses faintly with residual magic.",
}

HIDDEN_ITEMS = {
    "Cave Entrance": ["small key"],
    "Rocky Path": [],
    "Narrow Passage": [],
    "Goblin Cavern": ["goblin tooth"],
    "Treasure Chamber": ["silver chalice"],
    "Ancient Vault": [],
    "Crossroads": [],
    "Forgotten Armory": ["chainmail fragment"],
    "Underground Lake": ["waterlogged scroll"],
    "Rat Tunnels": ["rat whisker"],
    "Ancient Library": [],
    "Meditation Chamber": [],
    "Hidden Passage": ["ancient talisman"],
    "Dragon's Lair": ["dragon scale"],
    "Escape Tunnel": [],
    "Sunlit Valley": [],
    "Healing Spring": ["greater health potion"],
}


class EventSystem:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable):
        if event in self.listeners:
            self.listeners[event].remove(handler)

    def emit(self, event: str, *args, **kwargs):
        if event in self.listeners:
            for handler in self.listeners[event]:
                handler(*args, **kwargs)


class Room:
    def __init__(self, name: str, data: RoomData):
        self.name = name
        self.data = data
        self.static_description = data.static_description or data.description
        self.items = list(data.items)
        self.enemies = list(data.enemies)
        self.exits = {k: v for k, v in data.exits.items()}

    def add_item(self, item: str):
        self.items.append(item)

    def remove_item(self, item: str):
        if item in self.items:
            self.items.remove(item)

    def can_exit(self, direction: str, player_inventory: List[str]) -> bool:
        if direction not in self.exits:
            return False
        exit_data = self.exits[direction]
        if exit_data.required_item:
            return exit_data.required_item in player_inventory
        return True

    def get_exit_room(self, direction: str) -> Optional[str]:
        if direction in self.exits:
            return self.exits[direction].room
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.data.description,
            "static_description": self.static_description,
            "items": list(self.items),
            "enemies": list(self.enemies),
            "exits": {k: v.model_dump() for k, v in self.exits.items()},
        }


class Player:
    def __init__(self, name: str = "Hero"):
        self.name = name
        self.health = 100
        self.inventory: List[str] = []

    def add_to_inventory(self, item: str):
        self.inventory.append(item)

    def remove_from_inventory(self, item: str):
        if item in self.inventory:
            self.inventory.remove(item)

    def has_item(self, item: str) -> bool:
        return item in self.inventory

    @property
    def block_chance(self) -> int:
        if any("shield" in i.lower() for i in self.inventory):
            return 50
        if any("helm" in i.lower() for i in self.inventory):
            return 25
        return 0

    def take_damage(self, damage: int) -> bool:
        self.health -= damage
        return self.health <= 0

    def status(self) -> str:
        items = ', '.join(self.inventory) if self.inventory else 'Empty'
        return f"Health: {self.health}, Inventory: {items}"


class World:
    def __init__(self, world_data: WorldData):
        self.start_room = world_data.start_room
        self.rooms: Dict[str, Room] = {
            name: Room(name, data) for name, data in world_data.rooms.items()
        }

    def get_room(self, name: str) -> Optional[Room]:
        return self.rooms.get(name)

    def get_start_room(self) -> Optional[Room]:
        return self.rooms.get(self.start_room)


class Game:
    def __init__(self, world: World):
        self.world = world
        self.player = Player()
        self.current_room = world.get_start_room()
        self.game_over = False
        self.events = EventSystem()
        self.recent_actions: deque = deque(maxlen=3)
        self.activity_log: deque = deque(maxlen=5)
        self.turn_count = 0
        self.status_effects: Dict[str, int] = {}
        self._found_hidden: set = set()
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        self.events.subscribe("player_dead", self._on_player_dead)

    def _on_player_dead(self):
        self.game_over = True

    def add_action(self, action: str):
        self.recent_actions.append(action)
        self.activity_log.append(action)

    def is_playing_aggressively(self) -> bool:
        aggressive = {"attack", "hit", "kill", "strike", "fight"}
        return any(any(kw in act for kw in aggressive) for act in self.recent_actions)

    def get_active_effects(self) -> List[str]:
        labels = []
        for effect, turns in self.status_effects.items():
            if turns > 0:
                if effect == "illuminated":
                    labels.append(f"[yellow]✦ Lit ({turns})[/]")
                elif effect == "empowered":
                    labels.append(f"[magenta]⚡ Empowered ({turns})[/]")
                elif effect == "shielded":
                    labels.append(f"[cyan]🛡 Shielded ({turns})[/]")
        return labels

    def tick_effects(self):
        expired = []
        for effect in self.status_effects:
            self.status_effects[effect] -= 1
            if self.status_effects[effect] <= 0:
                expired.append(effect)
        for e in expired:
            del self.status_effects[e]

    def move(self, direction: str) -> bool:
        if not self.current_room or not self.current_room.can_exit(
            direction, self.player.inventory
        ):
            return False
        next_name = self.current_room.get_exit_room(direction)
        if next_name:
            next_room = self.world.get_room(next_name)
            if next_room:
                self.current_room = next_room
                return True
        return False

    def pick_up_item(self, item: str):
        if item in self.current_room.items:
            self.current_room.remove_item(item)
            self.player.add_to_inventory(item)

    def drop_item(self, item: str):
        if item in self.player.inventory:
            self.player.remove_from_inventory(item)
            self.current_room.add_item(item)

    def attack(self) -> str:
        self.add_action("attack")
        if self.current_room.enemies:
            enemy = self.current_room.enemies.pop(0)
            damage = 10
            dead = self.player.take_damage(damage)
            if dead:
                self.events.emit("player_dead")
            return f"You attack the {enemy}! It strikes back for {damage} damage."
        else:
            damage = 5
            dead = self.player.take_damage(damage)
            if dead:
                self.events.emit("player_dead")
            return (
                f"You swing at the shadows and hit nothing. "
                f"You stumble and hurt yourself (-{damage} HP)."
            )

    def combat_round(self) -> str:
        self.add_action("attack")
        if not self.current_room.enemies:
            damage = random.randint(3, 7)
            dead = self.player.take_damage(damage)
            if dead:
                self.events.emit("player_dead")
            return f"▸ You swing at the shadows and hit nothing. You stumble (-{damage} HP)."

        enemy = self.current_room.enemies[0]
        blocked = False
        if self.player.block_chance > 0 and random.randint(1, 100) <= self.player.block_chance:
            blocked = True
            player_damage = 0
            self.add_action("blocked attack")
        else:
            player_damage = random.randint(5, 15)

        enemy_damage = random.randint(8, 18)
        enemy_defeated = False

        if "empowered" in self.status_effects:
            enemy_damage = int(enemy_damage * 1.5)

        self.add_action(f"dealt {enemy_damage} damage to {enemy}")
        if enemy_damage >= 15 or enemy_damage >= 12 and random.random() < 0.5:
            self.current_room.enemies.pop(0)
            enemy_defeated = True

        if not blocked:
            dead = self.player.take_damage(player_damage)
            if dead:
                self.events.emit("player_dead")

        if blocked:
            msg = f"▸ {enemy} attacks! You [bold cyan]block[/] with your shield!"
            if enemy_defeated:
                msg += f" You counter and [bold green]defeat[/] the {enemy}!"
        elif enemy_defeated:
            msg = f"▸ You [bold green]defeat[/] the {enemy}! It strikes back for [red]{player_damage}[/] damage."
        else:
            msg = f"▸ You strike the {enemy} for [yellow]{enemy_damage}[/] damage! It hits you for [red]{player_damage}[/]."

        if self.is_playing_aggressively() and random.random() < 0.3:
            extra = random.randint(2, 5)
            self.player.take_damage(extra)
            msg += f" In your aggression, you leave yourself open ([red]-{extra}[/])."

        return msg

    def use_item(self, item: str) -> str:
        if item not in self.player.inventory:
            return f"▸ You don't have [yellow]{item}[/]."

        effects = {
            "healing salve": lambda: self._use_healing_item(30, "healing salve"),
            "health potion": lambda: self._use_healing_item(50, "health potion"),
            "greater health potion": lambda: self._use_healing_item(75, "greater health potion"),
            "elven bread": lambda: self._use_healing_item(15, "elven bread"),
            "bandages": lambda: self._use_healing_item(10, "bandages"),
            "mysterious herb": lambda: self._use_healing_item(25, "mysterious herb"),
            "torch": lambda: self._use_torch(),
            "map": lambda: self._use_map(),
            "crystal focus": lambda: self._use_crystal_focus(),
            "rusty key": lambda: "[yellow]▸ The rusty key looks like it belongs to an old lock. Try it on locked doors.[/]",
        }

        if item in effects:
            self.add_action(f"used {item}")
            return effects[item]()
        return f"[yellow]▸ You can't figure out how to use {item}.[/]"

    def _use_healing_item(self, heal: int, item_name: str) -> str:
        old_hp = self.player.health
        self.player.health = min(100, old_hp + heal)
        actual_heal = self.player.health - old_hp
        self.player.remove_from_inventory(item_name)
        if actual_heal > 0:
            return f"[green]▸ You use {item_name}. [+{actual_heal} HP!] You feel restored.[/]"
        return f"[yellow]▸ You use {item_name} but you're already at full health.[/]"

    def _use_torch(self) -> str:
        self.status_effects["illuminated"] = 10
        return "[yellow]▸ You light the torch. The room glows with warm firelight. You can see details you missed before.[/]"

    def _use_map(self) -> str:
        self.status_effects["illuminated"] = 5
        revealed = []
        room = self.current_room
        for direction, exit_data in room.exits.items():
            target = self.world.get_room(exit_data.room)
            if target and target.items:
                revealed.append(f"{direction.upper()} → {exit_data.room} (has: {', '.join(target.items)})")
        base = "[green]▸ You study the ancient map. The passages become clear in your mind.[/]"
        if revealed:
            base += "\n" + "\n".join(f"  [dim]{r}[/]" for r in revealed)
        else:
            base += "\n  [dim]The map shows only darkness ahead...[/]"
        return base

    def _use_crystal_focus(self) -> str:
        self.status_effects["empowered"] = 5
        return "[magenta]▸ The crystal pulses with energy! You feel empowered. Your next attacks will be stronger.[/]"

    def examine_item(self, item: str) -> str:
        if item in self.player.inventory:
            location = "your inventory"
        elif item in self.current_room.items:
            location = "the room"
        else:
            return f"[red]▸ You don't see {item} anywhere.[/]"

        lore = ITEM_LORE.get(item)
        if lore:
            return f"[cyan]▸ {item}[/] ([dim]{location}[/])\n  {lore}"
        return f"[cyan]▸ {item}[/] ([dim]{location}[/])\n  [dim]A plain {item}. Nothing special.[/]"

    def search_room(self) -> str:
        room_name = self.current_room.name
        room_hidden = HIDDEN_ITEMS.get(room_name, [])
        newly_found = [h for h in room_hidden if h not in self._found_hidden]

        if not newly_found:
            return "[dim]▸ You search the room thoroughly but find nothing new.[/]"

        for h in newly_found:
            self._found_hidden.add(h)
            self.current_room.add_item(h)

        items_list = ", ".join(f"[yellow]{h}[/]" for h in newly_found)
        return f"[green]▸ You search carefully and discover: {items_list}![/]"

    def save_game(self, save_file: str = "savegame.json"):
        try:
            state = {
                "player": {
                    "health": self.player.health,
                    "inventory": self.player.inventory,
                },
                "current_room": self.current_room.name if self.current_room else None,
                "rooms": {
                    name: {
                        "items": room.items,
                        "enemies": room.enemies,
                    }
                    for name, room in self.world.rooms.items()
                },
            }
            with open(save_file, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception:
            pass

    def load_game(self, save_file: str = "savegame.json"):
        try:
            with open(save_file, 'r') as f:
                state = json.load(f)
            self.player.health = state["player"]["health"]
            self.player.inventory = state["player"]["inventory"]
            for name, rs in state["rooms"].items():
                room = self.world.get_room(name)
                if room:
                    room.items = rs["items"]
                    room.enemies = rs.get("enemies", [])
            room = self.world.get_room(state["current_room"])
            if room:
                self.current_room = room
        except Exception:
            pass
