import json
import random
from typing import Dict, List, Optional, Callable
from collections import deque
from src.models import WorldData, RoomData


ITEM_LORE = {
    "torch": "A simple wooden torch wrapped in oil-soaked cloth. It will light your way through the darkness.",
    "map": "A faded parchment map of the cave system. Several paths are marked in faded ink, including one that leads to sunlight.",
    "rusty key": "A heavily corroded iron key. The teeth are still intact despite the rust.",
    "ancient coin": "A gold coin from a forgotten era. One side bears a crowned skull, the other a coiled serpent.",
    "golden idol": "A fist-sized idol of pure gold, shaped like a crouching beast with emerald eyes.",
    "legendary blade": "A sword that hums with latent power. The blade is etched with ancient runes that pulse with blue light.",
    "healing salve": "A clay pot filled with a fragrant green ointment. It smells of mountain herbs and faint magic.",
    "shield": "A sturdy iron shield bearing the crest of a long-dead knightly order.",
    "iron helm": "A battle-worn iron helm padded with decayed leather.",
    "diamond ring": "A brilliant diamond ring set in silver. It catches the light even in darkness.",
    "ruby": "A blood-red ruby the size of your thumb that pulses with warm inner light.",
    "rusty sword": "A sword recovered from the lakebed. Pitted with rust but still dangerously sharp.",
    "ancient scroll": "A brittle scroll covered in ornate script from a forgotten language.",
    "crystal focus": "A clear crystal sphere that hums with contained energy.",
    "dragon heart": "The still-warm heart of an elder wyrm radiating immense primal power.",
    "gem of power": "A faceted gem glowing with captured starlight. You feel stronger holding it.",
    "gold coin": "A single warm gold coin, as if newly minted in this ancient place.",
    "ancient crown": "A crown of black iron and silver set with stones like captured moonlight.",
    "goblin tooth": "A sharp yellowed tooth from a goblin. Worth something to a collector.",
    "silver chalice": "An ornate silver chalice etched with vines and lunar phases.",
    "chainmail fragment": "A fragment of chainmail from a forgotten soldier. The rings are still strong.",
    "waterlogged scroll": "A scroll underwater for years. Most ink has run but a map fragment remains.",
    "rat whisker": "A long twitchy whisker from a giant rat.",
    "ancient talisman": "A stone talisman carved with protective runes humming faintly.",
    "dragon scale": "A single scale from an elder wyrm. Hot to the touch and shimmering with iridescent color.",
    "small key": "A small brass key that might open a chest or lockbox.",
    "health potion": "A glass vial of crimson liquid glowing with soft inner light. Restores 50 HP.",
    "greater health potion": "A larger vial of deep ruby liquid swirling like liquid fire. Restores 75 HP.",
    "elven bread": "Sweet elven bread wrapped in leaves. Smells of honey and wildflowers. Restores 15 HP.",
    "bandages": "Clean linen bandages for binding wounds. Restores 10 HP.",
    "mysterious herb": "A dried herb with silver veins pulsing with residual magic. Restores 25 HP.",
    "iron sword": "A solid iron blade, well-balanced and keen-edged. A reliable weapon.",
    "silver dagger": "A slender silver dagger that gleams with a faint enchantment. Quick and deadly.",
    "leather vest": "A toughened leather vest that offers modest protection.",
    "chainmail": "A shirt of interlocking metal rings. Sturdy and reliable armor.",
    "ring of strength": "A thick band of dark iron. Your muscles tense with power when you wear it.",
    "ring of protection": "A ring of polished stone. A shimmering barrier flickers around you.",
    "iron key": "A heavy iron key with intricate teeth. It looks important.",
    "silver key": "A delicate silver key that glows faintly. It opens something special.",
    "crystal key": "A key of pure crystal that refracts light into rainbows. It feels ancient.",
    "compass": "An ornate compass. The needle always points toward the nearest living soul.",
    "lantern": "A hooded lantern with an ever-burning flame inside. It casts a warm steady light.",
    "rope": "A coil of sturdy hempen rope. Useful for crossing chasms or climbing.",
    "bomb": "A spherical iron bomb with a short fuse. Could clear obstacles or damage enemies.",
    "strange mushroom": "A glowing purple mushroom that pulses with an otherworldly light.",
    "phoenix feather": "A single feather that smolders with eternal flame. It radiates hope.",
}

HIDDEN_ITEMS = {
    "Cave Entrance": ["small key"], "Rocky Path": [], "Narrow Passage": [],
    "Goblin Cavern": ["goblin tooth"], "Treasure Chamber": ["silver chalice"],
    "Ancient Vault": [], "Crossroads": [],
    "Forgotten Armory": ["chainmail fragment"],
    "Underground Lake": ["waterlogged scroll"],
    "Rat Tunnels": ["rat whisker"], "Ancient Library": [],
    "Meditation Chamber": [], "Hidden Passage": ["ancient talisman"],
    "Dragon's Lair": ["dragon scale"], "Escape Tunnel": [], "Sunlit Valley": [],
    "Healing Spring": ["greater health potion"],
    "Fungal Caverns": ["strange mushroom"], "Crystal Cave": [],
    "Lava Bridge": [], "Bazaar": [],
    "Oracle's Chamber": ["phoenix feather"],
    "Training Ground": [], "Armory Depths": ["iron sword"],
    "Treasury": [], "Deep Tunnels": [],
    "Underground River": [], "Silent Grove": ["elven bread"],
    "Bone Pit": ["ancient coin"], "Spider Nest": [],
    "Collapsed Tunnel": [], "Verdant Cavern": [],
    "Echoing Hall": [], "Ritual Chamber": [],
    "Tomb of Kings": ["ancient crown"], "Shadow Thief Lair": [],
    "Forgotten City Gates": [], "Market Ruins": ["silver key"],
}

EQUIPMENT_SLOTS = {
    "iron sword": "weapon", "silver dagger": "weapon", "legendary blade": "weapon",
    "rusty sword": "weapon", "shield": "weapon",
    "leather vest": "armor", "chainmail": "armor", "iron helm": "armor",
    "ring of strength": "accessory", "ring of protection": "accessory",
    "diamond ring": "accessory", "crystal focus": "accessory",
    "ancient talisman": "accessory", "gem of power": "accessory",
}

EQUIPMENT_STATS = {
    "iron sword": {"attack": 5}, "silver dagger": {"attack": 3},
    "legendary blade": {"attack": 10}, "rusty sword": {"attack": 2},
    "shield": {"defense": 5, "block": 25},
    "leather vest": {"max_hp": 15}, "chainmail": {"max_hp": 30},
    "iron helm": {"max_hp": 10, "defense": 3},
    "ring of strength": {"attack": 4},
    "ring of protection": {"defense": 5},
    "diamond ring": {"attack": 1, "defense": 1},
    "crystal focus": {"attack": 3, "max_hp": 5},
    "ancient talisman": {"defense": 3, "max_hp": 10},
    "gem of power": {"attack": 6, "max_hp": 5},
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


class GameNPC:
    def __init__(self, name: str, start_room: str, behavior: str, role: str, dialogue_tag: str):
        self.name = name
        self.current_room = start_room
        self.behavior = behavior
        self.role = role
        self.dialogue_tag = dialogue_tag
        self.talked_to = False

    def to_dict(self) -> dict:
        return {"name": self.name, "room": self.current_room, "role": self.role}


NPC_DEFS = [
    GameNPC("Shadow Thief", "Goblin Cavern", "roamer", "trickster", "shadow_thief"),
    GameNPC("Merchant Vex", "Bazaar", "stationary", "merchant", "merchant"),
    GameNPC("Oracle of the Deep", "Oracle's Chamber", "stationary", "oracle", "oracle"),
    GameNPC("Lost Soul", "Crossroads", "roamer", "guide", "lost_soul"),
    GameNPC("Ancient Guardian", "Tomb of Kings", "guard", "guardian", "guardian"),
    GameNPC("Wandering Bard", "Silent Grove", "roamer", "bard", "bard"),
]


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
            "name": self.name, "description": self.data.description,
            "static_description": self.static_description,
            "items": list(self.items), "enemies": list(self.enemies),
            "exits": {k: v.model_dump() for k, v in self.exits.items()},
        }


class Player:
    def __init__(self, name: str = "Hero"):
        self.name = name
        self.health = 100
        self.max_hp = 100
        self.inventory: List[str] = []
        self.equipment: Dict[str, Optional[str]] = {"weapon": None, "armor": None, "accessory": None}

    def add_to_inventory(self, item: str):
        self.inventory.append(item)

    def remove_from_inventory(self, item: str):
        if item in self.inventory:
            self.inventory.remove(item)

    def has_item(self, item: str) -> bool:
        return item in self.inventory

    @property
    def attack_bonus(self) -> int:
        bonus = 0
        for slot, item in self.equipment.items():
            if item and item in EQUIPMENT_STATS:
                bonus += EQUIPMENT_STATS[item].get("attack", 0)
        return bonus

    @property
    def defense_bonus(self) -> int:
        bonus = 0
        for slot, item in self.equipment.items():
            if item and item in EQUIPMENT_STATS:
                bonus += EQUIPMENT_STATS[item].get("defense", 0)
        return bonus

    @property
    def block_chance(self) -> int:
        base = 0
        for slot, item in self.equipment.items():
            if item and item in EQUIPMENT_STATS:
                base += EQUIPMENT_STATS[item].get("block", 0)
        if any("shield" in i.lower() for i in self.inventory if i not in self.equipment.values()):
            base += 25
        return min(base, 75)

    def recalc_max_hp(self):
        bonus = 0
        for slot, item in self.equipment.items():
            if item and item in EQUIPMENT_STATS:
                bonus += EQUIPMENT_STATS[item].get("max_hp", 0)
        self.max_hp = 100 + bonus
        self.health = min(self.health, self.max_hp)

    def take_damage(self, damage: int) -> bool:
        if damage < 0:
            self.health = min(self.max_hp, self.health - damage)
            return False
        reduced = max(0, damage - self.defense_bonus)
        self.health -= reduced
        return self.health <= 0

    def equip_item(self, item: str) -> str:
        if item not in self.inventory:
            return f"[red]▸ You don't have {item}.[/]"
        slot = EQUIPMENT_SLOTS.get(item)
        if not slot:
            unhandled_equip = {"rope", "bomb", "strange mushroom", "compass", "lantern",
                              "phoenix feather", "elven bread", "bandages", "mysterious herb",
                              "health potion", "greater health potion", "healing salve",
                              "torch", "map", "ancient scroll", "waterlogged scroll",
                              "gold coin", "diamond ring", "ruby", "ancient coin",
                              "silver chalice", "goblin tooth", "rat whisker", "dragon heart",
                              "dragon scale", "small key", "iron key", "silver key", "crystal key",
                              "golden idol", "ancient crown", "chainmail fragment",
                              "gem of power", "crystal focus", "ancient talisman",
                              "iron helm", "rusty key"}
            if item in unhandled_equip:
                return f"[yellow]▸ You can't equip {item}. Try using it instead.[/]"
            return f"[yellow]▸ You can't equip {item}.[/]"

        old = self.equipment[slot]
        if old:
            self.equipment[slot] = None
            self.recalc_max_hp()
            return f"[green]▸ You unequip {old} and equip {item}.[/]"
        self.equipment[slot] = item
        self.recalc_max_hp()
        return f"[green]▸ You equip {item}.[/]"

    def unequip_item(self, slot: str) -> str:
        item = self.equipment.get(slot)
        if not item:
            return f"[yellow]▸ Nothing equipped in {slot} slot.[/]"
        self.equipment[slot] = None
        self.recalc_max_hp()
        return f"[green]▸ You unequip {item}.[/]"

    def status(self) -> str:
        items = ', '.join(self.inventory) if self.inventory else 'Empty'
        return f"Health: {self.health}/{self.max_hp}, Inventory: {items}"


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
        self.npcs: List[GameNPC] = [GameNPC(n.name, n.current_room, n.behavior, n.role, n.dialogue_tag) for n in NPC_DEFS]
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

    def get_npcs_in_room(self, room_name: str) -> List[GameNPC]:
        return [n for n in self.npcs if n.current_room == room_name]

    def get_active_effects(self) -> List[str]:
        labels = []
        for effect, turns in self.status_effects.items():
            if turns > 0:
                if effect == "illuminated":
                    labels.append(f"[yellow]✦ Lit ({turns})[/]")
                elif effect == "empowered":
                    labels.append(f"[magenta]⚡ Empowered ({turns})[/]")
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
            for slot, equipped in self.player.equipment.items():
                if equipped == item:
                    self.player.equipment[slot] = None
            self.player.remove_from_inventory(item)
            self.current_room.add_item(item)
            self.player.recalc_max_hp()

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
            return (f"You swing at the shadows and hit nothing. "
                    f"You stumble and hurt yourself (-{damage} HP).")

    def combat_round(self) -> str:
        self.add_action("attack")
        if not self.current_room.enemies:
            damage = max(1, random.randint(3, 7) - self.player.defense_bonus)
            dead = self.player.take_damage(damage)
            if dead:
                self.events.emit("player_dead")
            return f"▸ You swing at shadows. You stumble (-{damage} HP)."

        enemy = self.current_room.enemies[0]
        blocked = False
        if self.player.block_chance > 0 and random.randint(1, 100) <= self.player.block_chance:
            blocked = True
            player_damage = 0
        else:
            base = random.randint(5, 15)
            player_damage = max(0, base - self.player.defense_bonus // 2)

        enemy_damage = random.randint(8, 18) + self.player.attack_bonus
        enemy_defeated = False

        if "empowered" in self.status_effects:
            enemy_damage = int(enemy_damage * 1.5)

        if enemy_damage >= 15 or (enemy_damage >= 10 and random.random() < 0.4):
            self.current_room.enemies.pop(0)
            enemy_defeated = True

        if not blocked:
            dead = self.player.take_damage(player_damage)
            if dead:
                self.events.emit("player_dead")

        if blocked:
            msg = f"▸ {enemy} attacks! You [bold cyan]block[/]!"
            if enemy_defeated:
                msg += f" You counter and [bold green]defeat[/] the {enemy}!"
        elif enemy_defeated:
            msg = f"▸ You [bold green]defeat[/] the {enemy}! It hits for [red]{player_damage}[/]."
        else:
            msg = f"▸ You strike the {enemy} for [yellow]{enemy_damage}[/]! It hits you for [red]{player_damage}[/]."

        if self.is_playing_aggressively() and random.random() < 0.3:
            extra = random.randint(2, 5)
            self.player.take_damage(extra)
            msg += f" Aggression leaves you open ([red]-{extra}[/])."

        return msg

    def use_item(self, item: str) -> str:
        if item not in self.player.inventory:
            return f"▸ You don't have [yellow]{item}[/]."

        effects = {
            "healing salve": lambda: self._use_healing(30, "healing salve"),
            "health potion": lambda: self._use_healing(50, "health potion"),
            "greater health potion": lambda: self._use_healing(75, "greater health potion"),
            "elven bread": lambda: self._use_healing(15, "elven bread"),
            "bandages": lambda: self._use_healing(10, "bandages"),
            "mysterious herb": lambda: self._use_healing(25, "mysterious herb"),
            "torch": lambda: self._use_torch(),
            "map": lambda: self._use_map(),
            "lantern": lambda: self._use_lantern(),
            "compass": lambda: self._use_compass(),
            "crystal focus": lambda: self._use_crystal_focus(),
            "rusty key": lambda: "[yellow]▸ Try it on locked doors.[/]",
            "iron key": lambda: "[yellow]▸ The iron key feels weighty with purpose.[/]",
            "silver key": lambda: "[yellow]▸ The silver key glows faintly. It yearns for a special lock.[/]",
            "crystal key": lambda: "[yellow]▸ The crystal key refracts light. It feels ancient and powerful.[/]",
            "strange mushroom": lambda: self._use_strange_mushroom(),
            "bomb": lambda: self._use_bomb(),
            "rope": lambda: "[yellow]▸ The rope could help you cross gaps or climb.[/]",
        }

        if item in effects:
            self.add_action(f"used {item}")
            return effects[item]()
        return f"[yellow]▸ You can't figure out how to use {item}.[/]"

    def _use_healing(self, heal: int, item_name: str) -> str:
        old_hp = self.player.health
        self.player.health = min(self.player.max_hp, old_hp + heal)
        actual = self.player.health - old_hp
        self.player.remove_from_inventory(item_name)
        if actual > 0:
            return f"[green]▸ You use {item_name}. [+{actual} HP!][/]"
        return f"[yellow]▸ Already at full health.[/]"

    def _use_torch(self) -> str:
        self.status_effects["illuminated"] = 10
        return "[yellow]▸ The torch blazes. The room glows with warm light.[/]"

    def _use_lantern(self) -> str:
        self.status_effects["illuminated"] = 30
        return "[green]▸ The lantern casts a steady glow. The darkness retreats.[/]"

    def _use_compass(self) -> str:
        nearby = [n.name for n in self.npcs if n.current_room == self.current_room.name]
        if nearby:
            return f"[cyan]▸ The compass needle steadies toward: {', '.join(nearby)}.[/]"
        adj = []
        for direction, exit_data in self.current_room.exits.items():
            adj.append(exit_data.room)
        return f"[cyan]▸ The compass needle drifts toward: {', '.join(adj[:2])}.[/]"

    def _use_map(self) -> str:
        self.status_effects["illuminated"] = 5
        revealed = []
        for direction, exit_data in self.current_room.exits.items():
            target = self.world.get_room(exit_data.room)
            if target and target.items:
                revealed.append(f"{direction.upper()} → {exit_data.room}")
        base = "[green]▸ You study the map. The passages become clear.[/]"
        if revealed:
            base += "\n" + "\n".join(f"  [dim]{r}[/]" for r in revealed)
        else:
            base += "\n  [dim]Only darkness ahead...[/]"
        return base

    def _use_crystal_focus(self) -> str:
        self.status_effects["empowered"] = 5
        return "[magenta]▸ The crystal pulses! You feel empowered (+5 turns).[/]"

    def _use_strange_mushroom(self) -> str:
        heal = random.randint(10, 40)
        self.player.health = min(self.player.max_hp, self.player.health + heal)
        self.player.remove_from_inventory("strange mushroom")
        return f"[magenta]▸ You eat the strange mushroom. It tastes of lightning! [+{heal} HP][/]"

    def _use_bomb(self) -> str:
        self.player.remove_from_inventory("bomb")
        if self.current_room.enemies:
            names = self.current_room.enemies.copy()
            self.current_room.enemies.clear()
            return f"[yellow]▸ BOOM! The bomb devastates the room! Defeated: {', '.join(names)}.[/]"
        return "[yellow]▸ BOOM! Rubble falls but nothing else happens. Good thing no one was here.[/]"

    def examine_item(self, item: str) -> str:
        if item in self.player.inventory:
            loc = "your inventory"
        elif item in self.current_room.items:
            loc = "the room"
        else:
            return f"[red]▸ You don't see {item} anywhere.[/]"
        lore = ITEM_LORE.get(item)
        if lore:
            slot = EQUIPMENT_SLOTS.get(item)
            extra = f" ({slot} slot)" if slot else ""
            return f"[cyan]▸ {item}[/][dim]{extra}[/] ([dim]{loc}[/])\n  {lore}"
        return f"[cyan]▸ {item}[/] ([dim]{loc}[/])\n  [dim]A plain {item}.[/]"

    def search_room(self) -> str:
        room_hidden = HIDDEN_ITEMS.get(self.current_room.name, [])
        newly = [h for h in room_hidden if h not in self._found_hidden]
        if not newly:
            return "[dim]▸ You search thoroughly but find nothing new.[/]"
        for h in newly:
            self._found_hidden.add(h)
            self.current_room.add_item(h)
        items_list = ", ".join(f"[yellow]{h}[/]" for h in newly)
        return f"[green]▸ You search carefully and discover: {items_list}![/]"

    def talk_to_npc(self, npc_name: str) -> Optional[str]:
        npcs = self.get_npcs_in_room(self.current_room.name)
        if not npcs:
            return "[dim]▸ No one here to talk to.[/]"
        target = None
        for n in npcs:
            if npc_name.lower() in n.name.lower():
                target = n
                break
        if not target:
            names = ", ".join(f"[cyan]{n.name}[/]" for n in npcs)
            return f"[yellow]▸ You see: {names}. Be more specific.[/]"
        target.talked_to = True
        self.add_action(f"talked to {target.name}")
        return None

    def get_npc_dialogue_tag(self, npc_name: str) -> Optional[str]:
        for n in self.npcs:
            if npc_name.lower() in n.name.lower():
                return n.dialogue_tag
        return None

    def trade_with_npc(self, give: str, want: str) -> str:
        npcs = self.get_npcs_in_room(self.current_room.name)
        merchant = next((n for n in npcs if n.role == "merchant"), None)
        if not merchant:
            return "[yellow]▸ No merchant here to trade with.[/]"
        if give not in self.player.inventory:
            return f"[red]▸ You don't have {give}.[/]"
        trades = {
            "gold coin": "health potion", "goblin tooth": "elven bread",
            "rat whisker": "bandages", "ancient coin": "torch",
            "ruby": "silver dagger", "diamond ring": "iron sword",
            "silver chalice": "chainmail", "dragon scale": "ring of protection",
            "goblin tooth": "rope", "small key": "strange mushroom",
        }
        if give in trades and trades[give] == want:
            self.player.remove_from_inventory(give)
            self.current_room.add_item(want)
            return f"[green]▸ Merchant Vex nods. You trade {give} for {want}.[/]"
        return (f"[yellow]▸ Merchant Vex examines your {give}. "
                f"'Not interested. Try something else.'[/]")

    def get_merchant_inventory(self) -> str:
        return ("[green]Merchant Vex's Wares:[/]\n"
                "  [yellow]health potion[/] (trade: [dim]gold coin[/])\n"
                "  [yellow]torch[/] (trade: [dim]ancient coin[/])\n"
                "  [yellow]silver dagger[/] (trade: [dim]ruby[/])\n"
                "  [yellow]iron sword[/] (trade: [dim]diamond ring[/])\n"
                "  [yellow]chainmail[/] (trade: [dim]silver chalice[/])\n"
                "  [yellow]ring of protection[/] (trade: [dim]dragon scale[/])\n"
                "  [yellow]elven bread[/] (trade: [dim]goblin tooth[/])\n"
                "  [yellow]bandages[/] (trade: [dim]rat whisker[/])\n"
                "  [yellow]rope[/] (trade: [dim]small key[/])\n"
                "  [yellow]strange mushroom[/] (trade: [dim]goblin tooth[/])")

    def save_game(self, save_file: str = "savegame.json"):
        try:
            state = {
                "player": {
                    "health": self.player.health, "max_hp": self.player.max_hp,
                    "inventory": self.player.inventory,
                    "equipment": self.player.equipment,
                },
                "current_room": self.current_room.name if self.current_room else None,
                "rooms": {
                    name: {"items": room.items, "enemies": room.enemies}
                    for name, room in self.world.rooms.items()
                },
                "npcs": [{"name": n.name, "room": n.current_room, "talked_to": n.talked_to} for n in self.npcs],
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
            self.player.max_hp = state["player"].get("max_hp", 100)
            self.player.inventory = state["player"]["inventory"]
            self.player.equipment = state["player"].get("equipment", {"weapon": None, "armor": None, "accessory": None})
            for name, rs in state["rooms"].items():
                room = self.world.get_room(name)
                if room:
                    room.items = rs["items"]
                    room.enemies = rs.get("enemies", [])
            room = self.world.get_room(state["current_room"])
            if room:
                self.current_room = room
            for npc_data in state.get("npcs", []):
                for npc in self.npcs:
                    if npc.name == npc_data["name"]:
                        npc.current_room = npc_data["room"]
                        npc.talked_to = npc_data.get("talked_to", False)
        except Exception:
            pass
