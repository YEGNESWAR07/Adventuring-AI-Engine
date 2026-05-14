import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import AsyncGroq

SYSTEM_PROMPT = """You are an elite, dark-fantasy Game Master. Your goal is to describe rooms and events in a text-adventure game.

Rules:
- Brevity: Keep descriptions to exactly 2-3 sentences.
- Atmosphere: Use sensory details (smell, sound, temperature) to build immersion.
- No Spoilers: Do not tell the player what to do or what items are important unless they are visible in the room.
- Consistency: Maintain a mysterious and slightly ominous tone.
- Context: Use the provided JSON data about the room to ensure your descriptions are factually accurate to the game world."""

NPC_SYSTEM_PROMPT = """You are a game AI controlling a non-player character in a dungeon crawl.
Respond with ONLY a single direction word (north, south, east, west).
Choose the direction that makes the most narrative sense for a sneaky thief character."""


class AINarrator:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        self.client = AsyncGroq(api_key=api_key) if api_key else None

    async def generate_room_desc(
        self,
        room_data: Dict[str, Any],
        player_state: Dict[str, Any],
        recent_actions: Optional[List[str]] = None,
        npc_info: Optional[str] = None,
    ) -> str:
        fallback = room_data.get("static_description") or room_data.get("description", "A dark room.")
        if not self.client:
            return fallback

        room_name = room_data.get("name", "Unknown")
        items = room_data.get("items", [])
        enemies = room_data.get("enemies", [])
        exits = list(room_data.get("exits", {}).keys())

        prompt = f"The player enters {room_name}. "
        prompt += f"Items visible: {', '.join(items) if items else 'nothing of note'}. "
        prompt += f"Exits: {', '.join(exits) if exits else 'none'}."
        if enemies:
            prompt += f" Danger: {', '.join(enemies)} present!"

        prompt += f" Player Health: {player_state.get('health', 100)}/100."

        if recent_actions:
            prompt += f" Recent events: {'; '.join(recent_actions)}."

        if npc_info:
            prompt += f" Nearby: {npc_info}."

        health = player_state.get("health", 100)
        if health < 30:
            prompt += (
                " The player's vision blurs—they are near collapse. "
                "Describe the room as disorienting, surreal, like a fever dream."
            )
        elif health == 100:
            prompt += (
                " The player is at peak strength. "
                "Describe the room with sharp, heroic, vivid clarity."
            )

        if player_state.get("aggressive", False):
            prompt += (
                " The player has been acting aggressively. "
                "Darken the atmosphere—make the room feel ominous."
            )

        prompt += " Describe in 2-3 vivid, sensory sentences."

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=150,
            )
            result = response.choices[0].message.content.strip()
            return result if result else fallback
        except Exception:
            return fallback

    async def generate_item_description(
        self,
        item_name: str,
        context: Optional[str] = None,
    ) -> Optional[str]:
        if not self.client:
            return None

        prompt = (
            f"Describe the item '{item_name}' in a dark fantasy text adventure game. "
            f"Use 1-2 vivid sentences. Include sensory details (sight, texture, smell). "
            f"Give it a mysterious or ancient history.\n"
        )
        if context:
            prompt += f"Context: {context}\n"

        prompt += f"Item: {item_name}\nDescription:"

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a lore master for a dark fantasy game. Describe items mysteriously and vividly in 1-2 sentences."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=80,
            )
            result = response.choices[0].message.content.strip()
            return result if result else None
        except Exception:
            return None

    async def generate_hint(
        self,
        room_data: Dict[str, Any],
        player_state: Dict[str, Any],
        turns_in_room: int,
    ) -> Optional[str]:
        if not self.client or turns_in_room < 3:
            return None

        room_name = room_data.get("name", "Unknown")
        items = room_data.get("items", [])
        enemies = room_data.get("enemies", [])
        exits = list(room_data.get("exits", {}).keys())

        prompt = (
            f"The player has been in {room_name} for {turns_in_room} turns. "
            f"Exits: {', '.join(exits)}. "
            f"Items: {', '.join(items) if items else 'none'}. "
        )
        if enemies:
            prompt += f"Enemies: {', '.join(enemies)}. "
        prompt += (
            "Give ONE short cryptic hint (1 sentence) about something "
            "the player might have missed or should try. Be mysterious but helpful."
        )

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a cryptic guide in a dark fantasy game. Give short mysterious hints."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=60,
            )
            result = response.choices[0].message.content.strip()
            return result if result else None
        except Exception:
            return None

    async def generate_npc_dialogue(
        self,
        npc_name: str,
        npc_role: str,
        room_name: str,
        player_state: Dict[str, Any],
        talked_before: bool = False,
    ) -> Optional[str]:
        if not self.client:
            return None

        greetings = {
            "merchant": "'Ah, a customer! Welcome to my humble stall.'" if not talked_before else "'Back again? Browse at your leisure.'",
            "oracle": "'I have seen you coming in the threads of fate.'" if not talked_before else "'The threads shift. Your path branches.'",
            "trickster": "'Heh. Didn't see me, did you?'" if not talked_before else "'You're getting warmer. Or colder. Hard to tell.'",
            "guide": "'You look lost. Most are, down here.'" if not talked_before else "'Still searching? The answer is closer than you think.'",
            "guardian": "'None shall pass without the king's blessing.'" if not talked_before else "'You return. The crown still awaits.'",
            "bard": "'A song for a coin, traveler? I know the ballads of this deep place.'" if not talked_before else "'I have a new verse for you…'",
        }

        greeting = greetings.get(npc_role, f"'{npc_name} regards you silently.'")
        if not talked_before:
            return f"[cyan]▸ {npc_name} says:[/] {greeting}"
        return f"[cyan]▸ {npc_name} says:[/] {greeting}"

    async def generate_npc_encounter(
        self,
        npc_name: str,
        player_room: str,
        player_state: Dict[str, Any],
    ) -> Optional[str]:
        if not self.client:
            return None

        prompt = (
            f"The {npc_name} has entered the same room as the player ({player_room}). "
            f"Player health: {player_state.get('health', 100)}/100. "
            f"Generate 1-2 sentences of flavor text describing the {npc_name}'s sudden appearance "
            f"and what they seem to be doing. Make it atmospheric and mysterious."
        )

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a dark fantasy game master. Describe NPC encounters vividly but briefly."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=80,
            )
            result = response.choices[0].message.content.strip()
            return result if result else None
        except Exception:
            return None

    async def move_npc(
        self,
        npc_name: str,
        current_room: str,
        available_exits: List[str],
        context: str = "",
    ) -> str:
        if not self.client or not available_exits:
            return available_exits[0] if available_exits else current_room

        prompt = (
            f"The {npc_name} is in {current_room}. "
            f"Available exits: {', '.join(available_exits)}. "
            f"{context}"
            f"Where should the {npc_name} move? Respond with ONLY the direction word."
        )

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": NPC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=10,
            )
            result = response.choices[0].message.content.strip().lower()
            for d in available_exits:
                if d in result:
                    return d
        except Exception:
            pass
        return available_exits[0]
