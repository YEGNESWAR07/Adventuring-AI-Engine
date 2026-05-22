import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError, Field


class ExitData(BaseModel):
    room: str
    required_item: Optional[str] = None


class DialogueNode(BaseModel):
    text: str
    choices: Dict[str, str] = Field(default_factory=dict) # Maps choice text to next node ID


class DialogueTreeData(BaseModel):
    nodes: Dict[str, DialogueNode] # Maps node ID to DialogueNode


class NPCData(BaseModel):
    id: str
    name: str
    role: str = "villager" # merchant, oracle, trickster, guide, guardian, bard, etc.
    description: str
    personality: str
    goals: List[str]
    dialogue_tree_id: Optional[str] = None
    trades: List[Dict[str, str]] = Field(default_factory=list) # List of {"give": "item", "get": "item"}
    current_state: Dict[str, Any] = Field(default_factory=dict) # For tracking NPC-specific state


class LoreData(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


class RoomData(BaseModel):
    description: str
    static_description: str = ""
    items: List[str] = Field(default_factory=list)
    enemies: List[str] = Field(default_factory=list)
    exits: Dict[str, ExitData] = Field(default_factory=dict)
    npcs: List[NPCData] = Field(default_factory=list) # Added NPCs to RoomData


class WorldData(BaseModel):
    start_room: str
    rooms: Dict[str, RoomData]
    dialogue_trees: Dict[str, DialogueTreeData] = Field(default_factory=dict) # Added dialogue trees
    lore_entries: List[LoreData] = Field(default_factory=list) # Added lore entries


def load_world(path: str) -> WorldData:
    try:
        with open(path, 'r') as f:
            raw = json.load(f)
        return WorldData(**raw)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    except ValidationError as e:
        raise ValueError(f"World data validation error in {path}: {e}") from e
