# Adventuring AI Engine ⚡

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![Groq](https://img.shields.io/badge/AI-Groq%20LPU-orange)](https://groq.com)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Tests](https://img.shields.io/badge/tests-144%20passing-brightgreen)

> **An async AI-powered terminal-based interactive fiction engine.** Explore a vast 45-room dungeon, trade with unique NPCs, equip weapons and armor, fight dynamic turn-based combat, and uncover hidden secrets — all powered by Groq's LPU inference for real-time AI narration.


---
## 📊 At a Glance

| Feature | Detail |
|---------|--------|
| **World Size** | 45 interconnected rooms across 5 zones |
| **NPCs** | Multi-agent NPCs with unique Groq-powered personalities |
| **Items** | 40+ items with RAG-grounded lore and equipment slots |
| **Lore Engine** | Persistent RAG system using ChromaDB for deep world grounding |
| **Campaigns** | Persistent session tracking with branching narrative state |
| **Combat** | Dynamic turn-based with shield blocking and status effects |
| **AI Narration** | Groq Llama 3.3 70B for lore-consistent storytelling |
| **Tests** | 144 passing unit tests |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  [ User Input ]  →  [ Engine Logic ]  →  [ Pydantic ]     │
│                         │                       │          │
│                         ▼                       ▼          │
│                 [ Game State ]  ←  [ World Data ]          │
│                         │                │                  │
│                         ▼                ▼                  │
│  [ Rich TUI ]  ←  [ AsyncGroq ]  ←  [ Lore DB (RAG) ]      │
└─────────────────────────────────────────────────────────────┘
```

- **RAG Grounding** — Uses ChromaDB and `all-MiniLM-L6-v2` to retrieve relevant world history and item backstories, ensuring the narrator and NPCs are grounded in consistent lore.
- **Multi-Agent NPCs** — Individual NPCs have their own conversation memory and Groq-powered personas, allowing for natural dialogue and autonomous behavior.
- **Campaign Persistence** — Tracks global world state and player choices across sessions via `CampaignManager`.

---

## Features

### 📚 RAG-based World Lore
- **Vectorized Lore Database** — The `LoreManager` uses ChromaDB to store and retrieve world history, character bios, and item legends.
- **Grounded Narration** — Room descriptions and item examinations are automatically grounded in retrieved lore snippets, creating a rich, consistent world.
- **Persistent Lore** — World data is indexed once and persists across game runs in `data/lore_db`.

### 🎭 Multi-Agent NPC System
- **Independent Personalities** — Each NPC (Merchant, Oracle, Thief, etc.) is powered by its own Groq agent with unique system prompts and goals.
- **Natural Language Dialogue** — Talk to NPCs using natural language: `talk vex what do you know about the crystal?`.
- **Autonomous Behavior** — NPCs can roam the world or stay put based on their defined goals.

### 📜 Persistent Campaign Mode
- **Session Tracking** — The `CampaignManager` remembers your choices, discovered secrets, and world-altering events.
- **Global Flags** — Actions like defeating specific enemies or finding legendary items set permanent flags that influence the story across runs.

### 🧠 Context-Aware AI Narration
- **Real-time Groq inference** via `llama-3.3-70b-versatile` — each room entry generates a unique, sensory-rich description.
- **Sentiment memory** — The narrator tracks your last 3 actions. Aggressive play darkens the atmosphere; low HP triggers surreal descriptions.

### 💾 Stateful Session Management
- **Save/Load** — Full game state serialization (health, inventory, room states, NPC positions).
- **Campaign Persistence** — World state and narrative progress persist in `data/campaign.json`.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| AI Inference | Groq SDK (`AsyncGroq`) — Llama 3.3 70B |
| Vector DB | ChromaDB (Persistent Storage) |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Data Validation | Pydantic v2 |
| Terminal UI | Rich 14+ (`Live`, `Layout`, `Panel`, `Bar`) |
| Testing | `pytest` |

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

# 3. Configure your API key in .env
GROQ_API_KEY=gsk_your_key_here
```

### Run the Game

```bash
python -m src.main
```

---

## Gameplay Commands

| Command | Description |
|---------|-------------|
| `n` / `s` / `e` / `w` | Move in a cardinal direction |
| `talk <npc> <msg>` | Talk to an NPC using natural language |
| `examine <item>` | Examine an item with RAG-grounded lore |
| `inventory` / `i` | Show all items you are carrying |
| `search` | Search the room for hidden items |
| `pickup <item>` | Add an item to your inventory |
| `drop <item>` | Remove an item from your inventory |
| `attack` / `fight` | Engage enemies in dynamic combat |
| `save` / `load` | Persist or restore game state |
| `help` | Display command reference |
| `quit` | Exit the game |

---

## License

MIT License
Copyright (c) 2025 Pallapothu Yegneswar Gupta
rnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
