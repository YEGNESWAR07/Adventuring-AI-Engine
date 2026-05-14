import json
from typing import Dict, List, Optional
from pydantic import BaseModel, ValidationError


class ExitData(BaseModel):
    room: str
    required_item: Optional[str] = None


class RoomData(BaseModel):
    description: str
    static_description: str = ""
    items: List[str] = []
    enemies: List[str] = []
    exits: Dict[str, ExitData] = {}


class WorldData(BaseModel):
    start_room: str
    rooms: Dict[str, RoomData]


def load_world(path: str) -> WorldData:
    try:
        with open(path, 'r') as f:
            raw = json.load(f)
        return WorldData(**raw)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    except ValidationError:
        raise
