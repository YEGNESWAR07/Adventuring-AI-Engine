from groq import AsyncGroq
from typing import List, Dict, Any, Optional
from src.models import NPCData

class NPCAgent:
    def __init__(self, npc_data: NPCData, groq_client: AsyncGroq):
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
            f"Do not break character or mention being an AI. Keep responses brief (1-3 sentences)."
        )
        self.conversation_history.append({"role": "system", "content": system_message})

    async def generate_dialogue(self, player_input: str, game_context: str, lore_context: Optional[str] = None) -> str:
        # Construct the context-aware prompt
        full_context = f"Current game context: {game_context}"
        if lore_context:
            full_context += f"\n\n{lore_context}"
        
        # We don't want to keep growing the system message with context, 
        # so we inject context as a reminder or part of the user message.
        # For now, let's update the system message with current context.
        base_system = (
            f"You are {self.npc_data.name}, a {self.npc_data.personality} NPC. "
            f"Goals: {', '.join(self.npc_data.goals)}. "
            f"Current state: {self.npc_data.current_state}.\n"
            f"{full_context}"
        )
        self.conversation_history[0]["content"] = base_system

        self.conversation_history.append({"role": "user", "content": player_input})

        try:
            chat_completion = await self.groq_client.chat.completions.create(
                messages=self.conversation_history,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=150,
            )
            npc_response = chat_completion.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": npc_response})
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-9:]
                
            return npc_response
        except Exception as e:
            print(f"Error generating dialogue for {self.npc_data.name}: {e}")
            return f"{self.npc_data.name} regards you with a strange look, but says nothing."

    def reset_conversation(self):
        self._initialize_conversation_history()
