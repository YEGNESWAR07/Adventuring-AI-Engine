# Aura-Quest ⚡ — An Async AI-Powered Adventure Engine

> **Terminal-based interactive fiction** powered by Groq's LPU inference, Pydantic-validated world state, and a Rich real-time TUI.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  [ User Input ]  →  [ Engine Logic ]  →  [ Pydantic ]     │
│                         │                       │          │
│                         ▼                       ▼          │
│                 [ Game State ]  ←  [ World Data ]          │
│                         │                                   │
│                         ▼                                   │
│  [ Rich TUI ]  ←  [ AsyncGroq Narrator ]                   │
└─────────────────────────────────────────────────────────────┘
```

- **AsyncGroq** — Non-blocking LLM inference via Groq's LPU™ hardware; sub-500ms narration latency keeps the UI responsive.
- **Pydantic v2** — Schema-driven world building; `WorldData`, `RoomData`, and `ExitData` models validate `world.json` at load, catching malformed data before runtime.
- **Object-Oriented Engine** — Clean separation of concerns: `World` owns rooms, `Game` orchestrates state, `Player` manages inventory/health, `EventSystem` decouples side-effects.

---

## Features

### 🧠 Context-Aware AI Narration
- **Real-time Groq inference** via `llama-3.3-70b-versatile` — each room entry generates a unique, sensory-rich description.
- **Sentiment memory** — The narrator tracks your last 3 actions. Aggressive play darkens the atmosphere; low HP triggers surreal, fever-dream descriptions.
- **Graceful fallback** — Returns `static_description` from JSON if the API is unavailable.

### 🖥️ Real-Time TUI Layout
- **Rich `Live` display** with a four-panel cockpit layout (20/60/20 + input bar):
  - **Left**: Player stats (HP bar, turn counter, room, mood) + Mini-map (connected rooms + lock indicators)
  - **Center**: AI story feed with room items & enemies displayed inline beneath narration
  - **Right**: Discovery log (items collected + NPCs met)
  - **Bottom**: Input command bar showing prompt state
- **Startup welcome panel** — Displays a full list of available commands on first launch; auto-dismisses after the player's first command.
- **Typing indicator** — Shows `✦ The narrator is weaving the story...` while the AI generates room descriptions, giving real-time feedback during async LLM calls.
- **Character-by-character input** — Uses `msvcrt.getwch()` for real-time keystroke capture; each character appears instantly in the input bar panel as you type. No more typing "in the background."
- **Async non-blocking architecture** — Input reading runs in a thread via `asyncio.to_thread`, never blocking the render loop.

### 👤 Agentic NPC — "The Shadow Thief"
- **Autonomous roaming** — Every 5 turns, Groq decides where the Shadow Thief moves next, creating a living world that evolves around you.
- **Dynamic encounters** — The NPC can appear in any room, adding unpredictability to every playthrough. A special alert fires when the thief enters your room.

### 🎮 New Interactive Commands
- **`inventory` / `i`** — Opens a dedicated inventory panel showing all carried items with a numbered list.
- **`examine <item>`** — Reveals rich item lore (hand-written descriptions + optional AI-enhanced narration via Groq).
- **`use <item>`** — Interactive item effects: `healing salve` (+30 HP), `health potion` (+50 HP), `greater health potion` (+75 HP), `torch` illuminates the area, `map` reveals room contents, `crystal focus` empowers attacks.
- **`search`** — Discovers hidden items in rooms that don't appear on first entry (lootable secrets in every major area).

### ⚔️ Dynamic Combat System
- **Variable damage** — Attacks deal 5-15 damage (enemies) and 8-18 damage (player), making each fight unpredictable.
- **Shield blocking** — Carrying a `shield` gives 50% block chance; an `iron helm` gives 25%. Blocked attacks deal zero damage.
- **Empowered state** — Using the `crystal focus` grants a 5-turn damage boost.
- **Aggression penalty** — Repeated aggressive play risks leaving yourself open to extra damage.
- **Enemy defeat chance** — Strong hits can instantly defeat enemies.

### 🩺 Status Effects & Visual Feedback
- **Active effects** — Status icons (`Lit`, `Empowered`) appear in the stats panel with turn-countdown timers.
- **Low HP warning** — HP bar blinks red and panel borders turn red when health drops below 25%.
- **NPC proximity alert** — A `⚠` icon appears in the room name when the Shadow Thief is in your room.
- **End-game stats** — Final screen shows turns survived and items collected.

### 💾 Stateful Session Management
- **Save/Load** — Full game state serialization (health, inventory, room states, enemy positions).
- **Turn tracking** — Activity log and aggression tracker persist across sessions.

---

## Installation & Setup

### Prerequisites
- **Python 3.12+**
- **Groq API key** (free at [console.groq.com](https://console.groq.com))

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/aura-quest.git
cd aura-quest

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your own API key
echo "GROQ_API_KEY=gsk_your_key_here" 
```



### Run the Game

```bash
python -m src.main
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| AI Inference | Groq SDK (`AsyncGroq`) — Llama 3.3 70B |
| Data Validation | Pydantic v2 |
| Terminal UI | Rich 14+ (`Live`, `Layout`, `Panel`, `Bar`) |
| Environment | `python-dotenv` |
| Testing | `unittest` + `pytest` |

---

## Project Structure

```
aura-quest/
├── .env                        # API keys (excluded from git)
├── .gitignore                  # Security exclusions
├── requirements.txt            # Python dependencies
├── README.md                   # You are here
├── savegame.json               # Auto-generated save file (excluded from git)
├── data/
│   └── world.json              # 20-room game world (Pydantic-validated)
├── src/
│   ├── __init__.py             # Package marker
│   ├── models.py               # Pydantic schemas (WorldData, RoomData, ExitData)
│   ├── engine.py               # Core logic (movement, inventory, combat, save/load)
│   ├── narrator.py             # AsyncGroq narrator + system prompts
│   ├── ui.py                   # Rich TUI components (panels, layout, input bar)
│   └── main.py                 # Async entry point + game loop
└── tests/
    └── test_engine.py          # Unit tests
```

---

## Gameplay

### First-Time Experience
When you start the game, a **welcome panel** greets you with the full list of commands. This panel disappears after your **first command**, transitioning seamlessly into the live story feed. Type `help` at any time to see the command list again.

### Commands

| Command | Description |
|---------|-------------|
| `n` / `s` / `e` / `w` / `ne` | Move in a cardinal or diagonal direction |
| `look` | Examine the room (uses static description — saves API calls) |
| `inventory` / `i` | Show all items you are carrying |
| `examine <item>` | Get a detailed description of an item |
| `use <item>` | Use an item (heal with salve, light torch, study map, etc.) |
| `search` | Search the room for hidden items |
| `pickup <item>` | Add an item to your inventory |
| `drop <item>` | Remove an item from your inventory |
| `attack` / `fight` | Engage enemies in dynamic combat |
| `save` | Persist game state to disk |
| `load` | Restore game state from disk |
| `help` | Display command reference |
| `quit` | Exit the game |

### Interactive UI Feedback
- **Room items & enemies** — Always visible beneath the AI narration in the center panel. See exactly what's in the room at a glance.
- **Inventory panel** — The `inventory`/`i` command switches the center panel to a numbered item list showing everything you carry.
- **Status effects** — Active buffs (`Lit`, `Empowered`) appear in the stats panel with turn-countdown timers.
- **Dynamic borders** — Panel borders change color based on health (blue > yellow > red) for at-a-glance status awareness.
- **Low HP blink** — The HP bar enters `blink` mode when health drops below 25%.
- **Turn counter** — Tracks every action you take, displayed in the left stats panel.
- **Command log** — Shows your 6 most recent actions with color-coded feedback (green=success, red=error, yellow=warning).
- **Typing indicator** — While the AI generates a room description, the center panel displays a loading animation for real-time feedback.
- **NPC proximity alert** — A `⚠` icon flashes next to the room name when the Shadow Thief is nearby.
- **Real-time input bar** — Type directly into the input bar panel at the bottom of the screen. Each keystroke appears instantly with a blinking cursor — no more typing in the terminal background.
- **Live AI hints** — If you linger in a room for 3+ turns, a mysterious voice whispers cryptic hints generated by Groq, making the AI feel present and helpful.
- **NPC encounter narration** — When the Shadow Thief enters your room, Groq generates unique atmospheric flavor text describing their appearance and actions.
- **Optimized API usage** — AI narration only triggers on room entry (not on `look`). Static descriptions and hand-written lore handle routine interactions, keeping API consumption efficient.

### World Map (20 Rooms)

```
Cave Entrance → Rocky Path → Narrow Passage → Goblin Cavern ───→ Crossroads ──→ Healing Spring
                                                    │                 │
                                                    │          ┌──────┼──────┬──────┐
                                                    ▼          ▼      ▼      ▼      ▼
                                            Ancient Vault   Armory  Lake  Library  Collapsed
                                            (requires:           │      │         Tunnel
                                             golden idol)        │      │           │
                                                        Echoing Hall    Verdant    │
                                                              │          Cavern    │
                                                              ▼                  ▼
                                                        Hidden Passage     Rat Tunnels
                                                              │
                                                              ▼
                                                         Dragon's Lair
                                                              │
                                                              ▼
                                                         Escape Tunnel
                                                              │
                                                              ▼
                                                         Sunlit Valley
                                                        (VICTORY)
```

---

## Future Roadmap

### Multi-Agent NPCs 🎭
Extend the agentic NPC system to support multiple independent characters with distinct personalities, goals, and dialogue trees — each powered by its own Groq agent.

### RAG-based World Lore 📚
Implement Retrieval-Augmented Generation to ground the AI narrator in a vector database of world history, item backstories, and NPC biographies — enabling deep, lore-consistent narratives.

### Persistent Campaign Mode 📜
Add session tracking that remembers player choices across runs, creating a branching narrative that unfolds over multiple play sessions.

---

## License

MIT
