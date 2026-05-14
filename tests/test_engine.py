import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque
from src.models import WorldData, RoomData, ExitData, ValidationError, load_world
from src.engine import World, Game, Room, Player, EventSystem
from src.narrator import AINarrator


DEFAULT_WORLD_DATA_DICT = {
    "start_room": "Entrance",
    "rooms": {
        "Entrance": {
            "description": "You are at the entrance.",
            "static_description": "You are at the entrance of a dark cave.",
            "items": ["torch", "map"],
            "enemies": [],
            "exits": {
                "north": {"room": "Hallway", "required_item": None}
            },
        },
        "Hallway": {
            "description": "A narrow hallway.",
            "static_description": "A narrow hallway stretches before you.",
            "items": ["key", "ancient coin"],
            "enemies": ["goblin"],
            "exits": {
                "south": {"room": "Entrance", "required_item": None},
                "east": {"room": "Treasure Room", "required_item": None},
                "north": {"room": "Vault", "required_item": "gold key"},
            },
        },
        "Treasure Room": {
            "description": "A glittering room.",
            "static_description": "A room glittering with gold and jewels.",
            "items": ["gold key"],
            "enemies": [],
            "exits": {
                "west": {"room": "Hallway", "required_item": None}
            },
        },
        "Vault": {
            "description": "An ancient vault.",
            "static_description": "You stand in an ancient vault.",
            "items": ["artifact"],
            "enemies": ["skeleton"],
            "exits": {
                "south": {"room": "Hallway", "required_item": None}
            },
        },
    },
}


def make_default_world_data() -> WorldData:
    return WorldData(**DEFAULT_WORLD_DATA_DICT)


def make_default_world() -> World:
    return World(make_default_world_data())


def make_default_game() -> Game:
    return Game(make_default_world())


class TestEventSystem(unittest.TestCase):
    def setUp(self):
        self.events = EventSystem()
        self.event_triggered = False
        self.arg_value = None

    def _handler(self):
        self.event_triggered = True

    def _handler_with_args(self, value):
        self.arg_value = value

    def test_subscribe_and_emit(self):
        self.events.subscribe("test_event", self._handler)
        self.events.emit("test_event")
        self.assertTrue(self.event_triggered)

    def test_unsubscribe(self):
        self.events.subscribe("test_event", self._handler)
        self.events.unsubscribe("test_event", self._handler)
        self.events.emit("test_event")
        self.assertFalse(self.event_triggered)

    def test_emit_with_no_listeners(self):
        self.events.emit("nonexistent_event")
        self.assertFalse(self.event_triggered)

    def test_unsubscribe_handler_not_subscribed(self):
        self.events.unsubscribe("test_event", self._handler)
        self.events.emit("test_event")
        self.assertFalse(self.event_triggered)

    def test_multiple_handlers(self):
        results = []
        def h1():
            results.append(1)
        def h2():
            results.append(2)
        self.events.subscribe("e", h1)
        self.events.subscribe("e", h2)
        self.events.emit("e")
        self.assertEqual(results, [1, 2])

    def test_emit_passes_args(self):
        self.events.subscribe("e", self._handler_with_args)
        self.events.emit("e", 42)
        self.assertEqual(self.arg_value, 42)

    def test_subscribe_same_handler_twice(self):
        self.events.subscribe("e", self._handler)
        self.events.subscribe("e", self._handler)
        self.events.emit("e")
        self.assertTrue(self.event_triggered)

    def test_emit_unknown_event(self):
        self.events.subscribe("a", self._handler)
        self.events.emit("b")
        self.assertFalse(self.event_triggered)

    def test_unsubscribe_nonexistent_event(self):
        self.events.unsubscribe("no_such", self._handler)


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player("TestHero")

    def test_initialization(self):
        self.assertEqual(self.player.name, "TestHero")
        self.assertEqual(self.player.health, 100)
        self.assertEqual(self.player.inventory, [])

    def test_add_to_inventory(self):
        self.player.add_to_inventory("sword")
        self.assertIn("sword", self.player.inventory)
        self.assertEqual(len(self.player.inventory), 1)

    def test_add_multiple(self):
        self.player.add_to_inventory("a")
        self.player.add_to_inventory("b")
        self.player.add_to_inventory("c")
        self.assertEqual(self.player.inventory, ["a", "b", "c"])

    def test_remove_from_inventory(self):
        self.player.add_to_inventory("sword")
        self.player.remove_from_inventory("sword")
        self.assertNotIn("sword", self.player.inventory)

    def test_remove_non_existent(self):
        self.player.remove_from_inventory("x")
        self.assertEqual(self.player.inventory, [])

    def test_remove_from_empty(self):
        self.player.remove_from_inventory("x")
        self.assertEqual(self.player.inventory, [])

    def test_take_damage(self):
        self.player.take_damage(30)
        self.assertEqual(self.player.health, 70)

    def test_take_damage_multiple(self):
        self.player.take_damage(20)
        self.player.take_damage(15)
        self.assertEqual(self.player.health, 65)

    def test_exact_death(self):
        dead = self.player.take_damage(100)
        self.assertEqual(self.player.health, 0)
        self.assertTrue(dead)

    def test_excessive_damage(self):
        dead = self.player.take_damage(150)
        self.assertEqual(self.player.health, -50)
        self.assertTrue(dead)

    def test_negative_damage_heals(self):
        self.player.take_damage(30)
        self.player.take_damage(-10)
        self.assertEqual(self.player.health, 80)

    def test_death_flag(self):
        result = self.player.take_damage(100)
        self.assertTrue(result)

    def test_not_dead(self):
        result = self.player.take_damage(50)
        self.assertFalse(result)

    def test_status_with_items(self):
        self.player.add_to_inventory("key")
        s = self.player.status()
        self.assertIn("Health: 100", s)
        self.assertIn("key", s)

    def test_status_empty(self):
        s = self.player.status()
        self.assertIn("Health: 100", s)
        self.assertIn("Empty", s)

    def test_status_after_damage(self):
        self.player.take_damage(25)
        s = self.player.status()
        self.assertIn("75", s)

    def test_add_duplicate(self):
        self.player.add_to_inventory("key")
        self.player.add_to_inventory("key")
        self.assertEqual(self.player.inventory, ["key", "key"])

    def test_remove_first_instance(self):
        self.player.add_to_inventory("key")
        self.player.add_to_inventory("key")
        self.player.remove_from_inventory("key")
        self.assertEqual(self.player.inventory, ["key"])


class TestRoom(unittest.TestCase):
    def setUp(self):
        data = RoomData(
            description="A test room",
            static_description="Static test room",
            items=["torch", "key"],
            enemies=[],
            exits={
                "north": ExitData(room="Next Room", required_item=None),
                "east": ExitData(room="Locked Vault", required_item="gold key"),
            },
        )
        self.room = Room("Test Room", data)

    def test_initialization(self):
        self.assertEqual(self.room.name, "Test Room")
        self.assertIn("torch", self.room.items)
        self.assertIn("north", self.room.exits)

    def test_default_items(self):
        room = Room("E", RoomData(description="d"))
        self.assertEqual(room.items, [])

    def test_default_exits(self):
        room = Room("E", RoomData(description="d"))
        self.assertEqual(room.exits, {})

    def test_default_enemies(self):
        room = Room("E", RoomData(description="d"))
        self.assertEqual(room.enemies, [])

    def test_enemies_from_constructor(self):
        data = RoomData(description="d", enemies=["goblin"])
        room = Room("D", data)
        self.assertEqual(room.enemies, ["goblin"])

    def test_static_description_fallback(self):
        data = RoomData(description="Short")
        room = Room("T", data)
        self.assertEqual(room.static_description, "Short")

    def test_custom_static(self):
        data = RoomData(description="S", static_description="Long fallback")
        room = Room("T", data)
        self.assertEqual(room.static_description, "Long fallback")

    def test_add_item(self):
        self.room.add_item("coin")
        self.assertIn("coin", self.room.items)

    def test_add_existing(self):
        self.room.add_item("torch")
        self.assertEqual(self.room.items.count("torch"), 2)

    def test_remove_item(self):
        self.room.remove_item("torch")
        self.assertNotIn("torch", self.room.items)

    def test_remove_nonexistent(self):
        self.room.remove_item("x")
        self.assertEqual(self.room.items, ["torch", "key"])

    def test_can_exit_no_required(self):
        self.assertTrue(self.room.can_exit("north", []))

    def test_cannot_exit_without_required(self):
        self.assertFalse(self.room.can_exit("east", []))

    def test_can_exit_with_required(self):
        self.assertTrue(self.room.can_exit("east", ["gold key"]))

    def test_cannot_exit_bad_direction(self):
        self.assertFalse(self.room.can_exit("south", []))

    def test_get_exit_room(self):
        self.assertEqual(self.room.get_exit_room("north"), "Next Room")

    def test_get_exit_room_nonexistent(self):
        self.assertIsNone(self.room.get_exit_room("south"))

    def test_to_dict(self):
        d = self.room.to_dict()
        self.assertEqual(d["name"], "Test Room")
        self.assertIn("torch", d["items"])
        self.assertIn("north", d["exits"])


class TestWorld(unittest.TestCase):
    def test_load_valid(self):
        w = make_default_world()
        self.assertEqual(w.start_room, "Entrance")
        self.assertIn("Entrance", w.rooms)
        self.assertEqual(len(w.rooms), 4)

    def test_get_room(self):
        w = make_default_world()
        r = w.get_room("Entrance")
        self.assertIsInstance(r, Room)
        self.assertEqual(r.name, "Entrance")

    def test_get_nonexistent(self):
        w = make_default_world()
        self.assertIsNone(w.get_room("Nowhere"))

    def test_get_start_room(self):
        w = make_default_world()
        self.assertEqual(w.get_start_room().name, "Entrance")

    def test_room_items_loaded(self):
        w = make_default_world()
        self.assertIn("torch", w.get_room("Entrance").items)

    def test_room_enemies_loaded(self):
        w = make_default_world()
        self.assertIn("goblin", w.get_room("Hallway").enemies)

    def test_room_static_loaded(self):
        w = make_default_world()
        self.assertEqual(
            w.get_room("Entrance").static_description,
            "You are at the entrance of a dark cave.",
        )

    def test_room_exits_loaded(self):
        w = make_default_world()
        h = w.get_room("Hallway")
        self.assertIn("north", h.exits)
        self.assertIn("south", h.exits)
        self.assertIn("east", h.exits)


class TestLoadWorldFunction(unittest.TestCase):
    def test_load_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(DEFAULT_WORLD_DATA_DICT, f)
            path = f.name
        try:
            wd = load_world(path)
            self.assertIsInstance(wd, WorldData)
            self.assertEqual(wd.start_room, "Entrance")
            self.assertIn("Entrance", wd.rooms)
        finally:
            os.remove(path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_world("nonexistent.json")

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not json")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_world(path)
        finally:
            os.remove(path)

    def test_missing_required_fields(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"rooms": {}}, f)
            path = f.name
        try:
            with self.assertRaises(ValidationError):
                load_world(path)
        finally:
            os.remove(path)


class TestAINarrator(unittest.TestCase):
    def setUp(self):
        self.room_data = {
            "name": "Entrance",
            "description": "You are at the entrance.",
            "static_description": "You stand at the cave entrance.",
            "items": ["torch"],
            "exits": {"north": {"room": "Hallway", "required_item": None}},
            "enemies": [],
        }
        self.player_state = {"health": 100, "inventory": [], "aggressive": False}

    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_no_api_key(self):
        n = AINarrator()
        result = asyncio_run(n.generate_room_desc(self.room_data, self.player_state))
        self.assertEqual(result, "You stand at the cave entrance.")

    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_no_static(self):
        d = dict(self.room_data)
        d.pop("static_description")
        n = AINarrator()
        result = asyncio_run(n.generate_room_desc(d, self.player_state))
        self.assertEqual(result, "You are at the entrance.")

    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_no_description(self):
        d = {"name": "V", "items": [], "exits": {}, "enemies": []}
        n = AINarrator()
        result = asyncio_run(n.generate_room_desc(d, self.player_state))
        self.assertEqual(result, "A dark room.")

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_api_call_normal(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mock_choice = MagicMock()
        mock_choice.message.content = "The cave entrance looms."
        mock_inst.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mock_choice]))
        n = AINarrator()
        result = asyncio_run(n.generate_room_desc(self.room_data, self.player_state))
        self.assertEqual(result, "The cave entrance looms.")

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_api_low_health_adds_hallucination(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mc = MagicMock()
        mc.message.content = "Walls ripple..."
        mock_inst.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mc]))
        n = AINarrator()
        lo = {"health": 20, "inventory": [], "aggressive": False}
        asyncio_run(n.generate_room_desc(self.room_data, lo))
        call = mock_inst.chat.completions.create.call_args
        msg = call[1]["messages"][1]["content"]
        self.assertIn("disorienting", msg.lower())

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_api_aggressive_adds_dark_tone(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mc = MagicMock()
        mc.message.content = "Walls close in."
        mock_inst.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mc]))
        n = AINarrator()
        ag = {"health": 80, "inventory": [], "aggressive": True}
        asyncio_run(n.generate_room_desc(self.room_data, ag))
        call = mock_inst.chat.completions.create.call_args
        msg = call[1]["messages"][1]["content"]
        self.assertIn("aggressive", msg.lower())

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_api_fallback_on_exception(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mock_inst.chat.completions.create = AsyncMock(side_effect=Exception("fail"))
        n = AINarrator()
        result = asyncio_run(n.generate_room_desc(self.room_data, self.player_state))
        self.assertEqual(result, "You stand at the cave entrance.")

    @patch("src.narrator.load_dotenv")
    @patch.dict(os.environ, {}, clear=True)
    def test_move_npc_no_client_returns_first_exit(self, mock_load):
        n = AINarrator()
        result = asyncio_run(n.move_npc("Thief", "Room", ["north", "south"]))
        self.assertEqual(result, "north")

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_move_npc_returns_chosen_exit(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mc = MagicMock()
        mc.message.content = "east"
        mock_inst.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mc]))
        n = AINarrator()
        result = asyncio_run(n.move_npc("Thief", "Crossroads", ["north", "east", "west"]))
        self.assertEqual(result, "east")

    @patch("src.narrator.AsyncGroq")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True)
    def test_move_npc_fallback_on_exception(self, mock_groq_cls):
        mock_inst = MagicMock()
        mock_groq_cls.return_value = mock_inst
        mock_inst.chat.completions.create = AsyncMock(side_effect=Exception("fail"))
        n = AINarrator()
        result = asyncio_run(n.move_npc("Thief", "Crossroads", ["north", "east"]))
        self.assertEqual(result, "north")


def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


class TestGameWorldLoading(unittest.TestCase):
    def test_game_initialized(self):
        game = make_default_game()
        self.assertIsNotNone(game.current_room)
        self.assertEqual(game.current_room.name, "Entrance")

    def test_all_rooms_accessible(self):
        game = make_default_game()
        self.assertIn("Entrance", game.world.rooms)
        self.assertIn("Hallway", game.world.rooms)

    def test_no_start_room(self):
        wd = WorldData(start_room="Nowhere", rooms={
            "R": RoomData(description="d", items=[], enemies=[], exits={})
        })
        world = World(wd)
        game = Game(world)
        self.assertIsNone(game.current_room)
        self.assertFalse(game.game_over)


class TestGameSentiment(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()

    def test_recent_actions_empty(self):
        self.assertEqual(len(self.game.recent_actions), 0)

    def test_add_action(self):
        self.game.add_action("move north")
        self.assertEqual(list(self.game.recent_actions), ["move north"])

    def test_maxlen_three(self):
        for a in ["a", "b", "c", "d"]:
            self.game.add_action(a)
        self.assertEqual(list(self.game.recent_actions), ["b", "c", "d"])

    def test_not_aggressive_default(self):
        self.assertFalse(self.game.is_playing_aggressively())

    def test_aggressive_with_attack(self):
        self.game.add_action("attack")
        self.assertTrue(self.game.is_playing_aggressively())

    def test_aggressive_clears(self):
        self.game.add_action("attack")
        self.game.add_action("move n")
        self.game.add_action("look")
        self.game.add_action("pickup x")
        self.assertFalse(self.game.is_playing_aggressively())

    def test_activity_log(self):
        self.game.add_action("moved north")
        self.game.add_action("picked torch")
        self.assertEqual(list(self.game.activity_log), ["moved north", "picked torch"])
        self.assertEqual(len(self.game.activity_log), 2)

    def test_activity_log_maxlen(self):
        for i in range(6):
            self.game.add_action(f"action {i}")
        self.assertEqual(len(self.game.activity_log), 5)

    def test_turn_count(self):
        self.assertEqual(self.game.turn_count, 0)
        self.game.turn_count += 1
        self.assertEqual(self.game.turn_count, 1)


class TestGameCombat(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()

    def test_attack_enemy_damages(self):
        self.game.move("north")
        h = self.game.player.health
        self.game.attack()
        self.assertLess(self.game.player.health, h)

    def test_attack_removes_enemy(self):
        self.game.move("north")
        self.assertIn("goblin", self.game.current_room.enemies)
        self.game.attack()
        self.assertNotIn("goblin", self.game.current_room.enemies)

    def test_attack_no_enemy(self):
        h = self.game.player.health
        self.game.attack()
        self.assertEqual(self.game.player.health, h - 5)

    def test_attack_tracks_action(self):
        self.game.attack()
        self.assertIn("attack", list(self.game.recent_actions))

    def test_attack_can_kill(self):
        g = make_default_game()
        g.move("north")
        g.player.take_damage(90)
        g.attack()
        self.assertTrue(g.game_over)

    def test_attack_enemy_10_damage(self):
        self.game.move("north")
        self.game.attack()
        self.assertEqual(self.game.player.health, 90)

    def test_attack_message_with_enemy(self):
        self.game.move("north")
        msg = self.game.attack()
        self.assertIn("goblin", msg)

    def test_attack_message_no_enemy(self):
        msg = self.game.attack()
        self.assertIn("shadows", msg)


class TestGameSerialization(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()
        self.save_file = "test_save.json"

    def tearDown(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

    def test_save_creates_file(self):
        self.game.save_game(self.save_file)
        self.assertTrue(os.path.exists(self.save_file))

    def test_save_contains_player_data(self):
        self.game.player.add_to_inventory("test_item")
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertEqual(d["player"]["health"], 100)
        self.assertIn("test_item", d["player"]["inventory"])

    def test_save_contains_current_room(self):
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertEqual(d["current_room"], "Entrance")

    def test_save_contains_room_items(self):
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertIn("Entrance", d["rooms"])
        self.assertIn("Hallway", d["rooms"])

    def test_save_preserves_health(self):
        self.game.player.take_damage(40)
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertEqual(d["player"]["health"], 60)

    def test_load_restores_health(self):
        self.game.player.take_damage(25)
        self.game.player.add_to_inventory("sword")
        self.game.save_game(self.save_file)
        g2 = make_default_game()
        g2.load_game(self.save_file)
        self.assertEqual(g2.player.health, 75)
        self.assertIn("sword", g2.player.inventory)

    def test_load_restores_room_items(self):
        self.game.pick_up_item("torch")
        self.game.drop_item("torch")
        self.game.save_game(self.save_file)
        g2 = make_default_game()
        g2.load_game(self.save_file)
        self.assertIn("torch", g2.current_room.items)

    def test_load_restores_current_room(self):
        self.game.move("north")
        self.game.save_game(self.save_file)
        g2 = make_default_game()
        g2.load_game(self.save_file)
        self.assertEqual(g2.current_room.name, "Hallway")

    def test_load_file_not_found(self):
        g = make_default_game()
        g.load_game("no_such_file.json")
        self.assertEqual(g.current_room.name, "Entrance")

    def test_load_corrupted(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("bad")
            path = f.name
        try:
            g = make_default_game()
            g.load_game(path)
            self.assertEqual(g.current_room.name, "Entrance")
        finally:
            os.remove(path)

    def test_save_overwrites(self):
        self.game.save_game(self.save_file)
        self.game.player.add_to_inventory("new")
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertIn("new", d["player"]["inventory"])

    def test_save_remembers_enemies(self):
        self.game.move("north")
        self.game.attack()
        self.game.save_game(self.save_file)
        with open(self.save_file) as f:
            d = json.load(f)
        self.assertEqual(d["rooms"]["Hallway"]["enemies"], [])


class TestGameMovement(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()

    def test_starts_in_entrance(self):
        self.assertEqual(self.game.current_room.name, "Entrance")

    def test_move_north(self):
        self.assertTrue(self.game.move("north"))
        self.assertEqual(self.game.current_room.name, "Hallway")

    def test_move_south(self):
        self.game.move("north")
        self.game.move("south")
        self.assertEqual(self.game.current_room.name, "Entrance")

    def test_move_east(self):
        self.game.move("north")
        self.game.move("east")
        self.assertEqual(self.game.current_room.name, "Treasure Room")

    def test_move_west(self):
        self.game.move("north")
        self.game.move("east")
        self.game.move("west")
        self.assertEqual(self.game.current_room.name, "Hallway")

    def test_move_invalid(self):
        self.assertFalse(self.game.move("south"))
        self.assertEqual(self.game.current_room.name, "Entrance")

    def test_move_locked(self):
        self.game.move("north")
        self.assertFalse(self.game.move("north"))
        self.assertEqual(self.game.current_room.name, "Hallway")

    def test_full_puzzle_path(self):
        self.game.move("north")
        self.game.move("east")
        self.game.pick_up_item("gold key")
        self.game.move("west")
        self.game.move("north")
        self.assertEqual(self.game.current_room.name, "Vault")

    def test_full_loop(self):
        self.game.move("north")
        self.game.move("east")
        self.game.move("west")
        self.game.move("south")
        self.assertEqual(self.game.current_room.name, "Entrance")


class TestGameItems(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()

    def test_pick_up(self):
        self.game.pick_up_item("torch")
        self.assertIn("torch", self.game.player.inventory)
        self.assertNotIn("torch", self.game.current_room.items)

    def test_pick_up_nonexistent(self):
        self.game.pick_up_item("x")
        self.assertEqual(self.game.player.inventory, [])

    def test_pick_up_after_empty(self):
        self.game.pick_up_item("torch")
        self.game.pick_up_item("torch")
        self.assertEqual(self.game.player.inventory, ["torch"])

    def test_drop(self):
        self.game.pick_up_item("torch")
        self.game.drop_item("torch")
        self.assertNotIn("torch", self.game.player.inventory)
        self.assertIn("torch", self.game.current_room.items)

    def test_drop_nonexistent(self):
        self.game.drop_item("x")
        self.assertEqual(self.game.player.inventory, [])

    def test_drop_not_in_inventory(self):
        self.game.drop_item("torch")
        self.assertEqual(self.game.player.inventory, [])

    def test_pick_up_all(self):
        self.game.pick_up_item("torch")
        self.game.pick_up_item("map")
        self.assertEqual(len(self.game.player.inventory), 2)
        self.assertEqual(self.game.current_room.items, [])

    def test_items_persist_after_move(self):
        self.game.pick_up_item("torch")
        self.game.move("north")
        self.game.move("south")
        self.assertNotIn("torch", self.game.current_room.items)

    def test_dropped_item_persists_across_rooms(self):
        self.game.pick_up_item("torch")
        self.game.move("north")
        self.game.drop_item("torch")
        self.game.move("south")
        self.assertNotIn("torch", self.game.current_room.items)

    def test_pick_up_from_different_room(self):
        self.game.move("north")
        self.game.pick_up_item("key")
        self.assertIn("key", self.game.player.inventory)

    def test_pick_up_required_item(self):
        self.game.move("north")
        self.game.move("east")
        self.game.pick_up_item("gold key")
        self.assertIn("gold key", self.game.player.inventory)

    def test_drop_and_re_pickup(self):
        self.game.pick_up_item("torch")
        self.game.drop_item("torch")
        self.game.pick_up_item("torch")
        self.assertIn("torch", self.game.player.inventory)

    def test_drop_multiple(self):
        self.game.pick_up_item("torch")
        self.game.pick_up_item("map")
        self.game.drop_item("torch")
        self.game.drop_item("map")
        self.assertEqual(self.game.player.inventory, [])
        self.assertIn("torch", self.game.current_room.items)
        self.assertIn("map", self.game.current_room.items)


class TestGameEvents(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()

    def test_death_sets_game_over(self):
        called = []
        def h():
            called.append(True)
        self.game.events.subscribe("player_dead", h)
        self.game.player.take_damage(100)
        self.game.events.emit("player_dead")
        self.assertTrue(self.game.game_over)
        self.assertEqual(called, [True])

    def test_survives_damage(self):
        self.game.player.take_damage(50)
        self.assertFalse(self.game.game_over)


class TestGameSaveLoadIntegration(unittest.TestCase):
    def setUp(self):
        self.game = make_default_game()
        self.sf = "integration_test_save.json"

    def tearDown(self):
        if os.path.exists(self.sf):
            os.remove(self.sf)

    def test_save_and_continue(self):
        self.game.move("north")
        self.game.pick_up_item("key")
        self.game.save_game(self.sf)
        self.game.pick_up_item("ancient coin")
        self.assertIn("key", self.game.player.inventory)
        self.assertIn("ancient coin", self.game.player.inventory)

    def test_save_then_load(self):
        self.game.move("north")
        self.game.save_game(self.sf)
        g2 = make_default_game()
        g2.load_game(self.sf)
        self.assertEqual(g2.current_room.name, "Hallway")

    def test_multi_cycle(self):
        self.game.move("north")
        self.game.save_game(self.sf)
        g2 = make_default_game()
        g2.load_game(self.sf)
        g2.move("east")
        g2.pick_up_item("gold key")
        g2.save_game(self.sf)
        g3 = make_default_game()
        g3.load_game(self.sf)
        self.assertEqual(g3.current_room.name, "Treasure Room")
        self.assertIn("gold key", g3.player.inventory)

    def test_save_after_drop(self):
        self.game.pick_up_item("torch")
        self.game.move("north")
        self.game.drop_item("torch")
        self.game.save_game(self.sf)
        g2 = make_default_game()
        g2.load_game(self.sf)
        self.assertEqual(g2.current_room.name, "Hallway")
        self.assertIn("torch", g2.current_room.items)


class TestWorldDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.world = make_default_world()

    def test_exits_point_to_valid_rooms(self):
        for rn, room in self.world.rooms.items():
            for d, ex in room.exits.items():
                if ex.room:
                    self.assertIn(ex.room, self.world.rooms,
                                  f"'{rn}' exit '{d}' → non-existent '{ex.room}'")

    def test_rooms_have_description(self):
        for rn, room in self.world.rooms.items():
            self.assertTrue(room.data.description, f"'{rn}' has empty description")

    def test_has_start_room(self):
        self.assertIsNotNone(self.world.get_start_room())

    def test_room_set(self):
        expected = {"Entrance", "Hallway", "Treasure Room", "Vault"}
        self.assertEqual(set(self.world.rooms.keys()), expected)

    def test_gold_key_exists(self):
        found = any("gold key" in room.items for room in self.world.rooms.values())
        self.assertTrue(found)


class TestExitConsistency(unittest.TestCase):
    def setUp(self):
        self.world = make_default_world()

    def test_bi_directional(self):
        rev = {"north": "south", "south": "north", "east": "west", "west": "east"}
        for rn, room in self.world.rooms.items():
            for d, ex in room.exits.items():
                dest = ex.room
                if dest and dest in self.world.rooms:
                    dest_room = self.world.rooms[dest]
                    reverse = rev.get(d)
                    if reverse in dest_room.exits:
                        rev_dest = dest_room.exits[reverse].room
                        self.assertEqual(rev_dest, rn,
                                         f"Mismatch: {rn}.{d} → {dest} but {dest}.{reverse} → {rev_dest}")


class TestEdgeCases(unittest.TestCase):
    def test_empty_room_items(self):
        r = Room("E", RoomData(description="d", items=[]))
        r.remove_item("x")
        self.assertEqual(r.items, [])

    def test_negative_player_health(self):
        p = Player("T")
        p.take_damage(200)
        self.assertEqual(p.health, -100)

    def test_event_no_side_effects(self):
        ev = EventSystem()
        ev.subscribe("a", lambda: None)
        ev.subscribe("b", lambda: None)
        ev.unsubscribe("c", lambda: None)
        ev.emit("c")

    def test_game_over_flag(self):
        g = make_default_game()
        g.game_over = True
        self.assertTrue(g.game_over)

    def test_room_no_objects(self):
        r = Room("V", RoomData(description="Nothing"))
        self.assertEqual(r.items, [])
        self.assertEqual(r.exits, {})
        self.assertEqual(r.enemies, [])

    def test_game_new_no_actions(self):
        g = make_default_game()
        self.assertEqual(len(g.recent_actions), 0)
        self.assertFalse(g.is_playing_aggressively())

    def test_room_to_dict_includes_enemies(self):
        data = RoomData(description="d", enemies=["goblin"])
        r = Room("D", data)
        d = r.to_dict()
        self.assertEqual(d["enemies"], ["goblin"])

    def test_pydantic_exit_data(self):
        ex = ExitData(room="Vault", required_item="gold key")
        self.assertEqual(ex.room, "Vault")
        self.assertEqual(ex.required_item, "gold key")

    def test_pydantic_exit_data_no_required(self):
        ex = ExitData(room="Next")
        self.assertIsNone(ex.required_item)

    def test_world_data_from_dict(self):
        wd = WorldData(**DEFAULT_WORLD_DATA_DICT)
        self.assertIn("Entrance", wd.rooms)
        self.assertIsInstance(wd.rooms["Entrance"], RoomData)

    def test_world_data_validation_fails(self):
        with self.assertRaises(ValidationError):
            WorldData(start_room=123, rooms="invalid")


if __name__ == "__main__":
    unittest.main(verbosity=2)
