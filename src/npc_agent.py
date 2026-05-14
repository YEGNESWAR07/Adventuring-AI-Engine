import os
from groq import Groq
from typing import List, Dict, Any
from src.models import NPCData

class NPCAgent:
    def __init__(self, npc_data: NPCData, groq_client: Groq):
        self.npc_data = npc_data
        self.groq_client = groq_client
        self.conversation_history: List[Dict[str, str]] = []
        self._initialize_conversation_history()

    def _initialize_conversation_history(self):
        # System message to define NPC's persona
        system_message = (
            f"You are {self.npc_data.name}, a {self.npc_data.personality} NPC in a text adventure game. "
            f"Your goals are: {', '.join(self.npc_data.goals)}. "
            f"Your current state is: {self.npc_data.current_state}. "
            f"Respond concisely and in character, reflecting your personality and goals. "
            f"Do not break character or mention being an AI. Keep responses brief, like a text adventure NPC."
        )
        self.conversation_history.append({"role": "system", "content": system_message})

    def generate_dialogue(self, player_input: str, game_context: str) -> str:
        # Add game context to the system message for better grounding
        current_system_message = self.conversation_history[0]["content"]
        if "Current game context:" not in current_system_message:
            self.conversation_history[0]["content"] += f"\nCurrent game context: {game_context}"
        else:
            # Update context if it already exists
            self.conversation_history[0]["content"] = (
                current_system_message.split("Current game context:")[0].strip() +
                f"\nCurrent game context: {game_context}"
            )

        self.conversation_history.append({"role": "user", "content": player_input})

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=self.conversation_history,
                model="llama3-8b-8192", # Using a suitable Groq model
                temperature=0.7,
                max_tokens=100,
            )
            npc_response = chat_completion.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": npc_response})
            return npc_response
        except Exception as e:
            print(f"Error generating dialogue for {self.npc_data.name}: {e}")
            return f"The {self.npc_data.name} seems distracted and doesn't respond."

    def reset_conversation(self):
        self.conversation_history = []
        self._initialize_conversation_history()
