from typing import Optional, Dict, Any
from groq import Groq
from src.models import DialogueTreeData, NPCData
from src.npc_agent import NPCAgent
import os

class DialogueManager:
    def __init__(self, world_dialogue_trees: Dict[str, DialogueTreeData]):
        self.world_dialogue_trees = world_dialogue_trees
        self.active_npc_agent: Optional[NPCAgent] = None
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def start_conversation(self, npc_data: NPCData, game_context: str) -> str:
        self.active_npc_agent = NPCAgent(npc_data, self.groq_client)
        # Initial greeting from the NPC
        initial_prompt = f"Hello, {npc_data.name}. What brings you here?"
        return self.active_npc_agent.generate_dialogue(initial_prompt, game_context)

    def continue_conversation(self, player_input: str, game_context: str) -> str:
        if not self.active_npc_agent:
            return "You are not currently in a conversation."
        return self.active_npc_agent.generate_dialogue(player_input, game_context)

    def end_conversation(self):
        if self.active_npc_agent:
            self.active_npc_agent.reset_conversation()
            self.active_npc_agent = None
        return "You end the conversation."

    def get_active_npc_name(self) -> Optional[str]:
        return self.active_npc_agent.npc_data.name if self.active_npc_agent else None
