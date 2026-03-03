# src/modules/conversation_manager.py

"""
Conversation Manager Module
----------------------------
Maintains conversation history so the AI remembers context
across multiple turns in a single session.

Pure Python — no API calls needed.
"""

from datetime import datetime
from collections import deque


class ConversationManager:
    """
    Manages the state of a single conversation session.

    Each time a user starts talking to NeuroHealth, a new ConversationManager is created.
    It stores the back-and-forth messages and tracks health context over the session.
    """

    def __init__(self, session_id=None, max_history=10):
        """
        Initialize a new conversation session.

        max_history: How many message pairs to remember.
                     After this limit, oldest messages are dropped.
                     (LLMs have input limits, so we can't keep everything forever)
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.max_history = max_history

        # Store messages as a list of dicts: {"role": "user/assistant", "content": "..."}
        self.messages = deque(maxlen=max_history * 2)  # *2 because user + assistant pairs

        # Track health context across the conversation
        self.health_context = {
            "symptoms_mentioned": [],
            "urgency_history": [],
            "conditions_mentioned": [],
            "age_mentioned": None,
            "gender_mentioned": None,
            "medications_mentioned": [],
            "allergies_mentioned": [],
        }

        self.created_at = datetime.now()
        self.message_count = 0

    def add_user_message(self, message):
        """Add a user message to history."""
        self.messages.append({"role": "user", "content": message})
        self.message_count += 1

    def add_assistant_message(self, message):
        """Add an assistant response to history."""
        self.messages.append({"role": "assistant", "content": message})

    def update_health_context(self, extracted_symptoms=None, urgency_info=None):
        """Update accumulated health context from this conversation."""
        if extracted_symptoms:
            new_symptoms = [s.get("name", "") for s in extracted_symptoms.get("symptoms", [])]
            for s in new_symptoms:
                if s and s not in self.health_context["symptoms_mentioned"]:
                    self.health_context["symptoms_mentioned"].append(s)

        if urgency_info:
            self.health_context["urgency_history"].append({
                "turn": self.message_count,
                "level": urgency_info.get("level")
            })

    def get_history_as_messages(self):
        """Returns conversation history formatted for the LLM."""
        return list(self.messages)

    def get_health_summary(self):
        """Returns a plain-English summary of health context accumulated so far."""
        if not any(self.health_context.values()):
            return ""

        parts = []

        if self.health_context["symptoms_mentioned"]:
            symptoms = ", ".join(self.health_context["symptoms_mentioned"])
            parts.append(f"Symptoms mentioned so far: {symptoms}")

        if self.health_context["medications_mentioned"]:
            meds = ", ".join(self.health_context["medications_mentioned"])
            parts.append(f"Medications mentioned: {meds}")

        return ". ".join(parts)

    def should_ask_clarification(self):
        """
        Returns True if we should ask clarifying questions.
        """
        if self.message_count <= 2:
            return True
        if not self.health_context["urgency_history"]:
            return True
        return False

    def to_dict(self):
        """Converts session to dictionary (for saving to file/database)."""
        return {
            "session_id": self.session_id,
            "created_at": str(self.created_at),
            "message_count": self.message_count,
            "messages": list(self.messages),
            "health_context": self.health_context
        }
