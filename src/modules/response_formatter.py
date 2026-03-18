# src/modules/response_formatter.py

"""
Response Formatter Module
--------------------------
Formats the final response for the user:
1. Adds visual urgency indicators (🔴 Emergency, 🟡 Routine, etc.)
2. Structures the response with clear sections
3. Adds "What to do next" action items
4. Adds disclaimer

Pure Python — no API calls needed.
"""

# Urgency color codes and emoji
URGENCY_DISPLAY = {
    "EMERGENCY": {"emoji": "🔴", "label": "EMERGENCY", "color": "#FF0000"},
    "URGENT": {"emoji": "🟠", "label": "URGENT", "color": "#FF6600"},
    "SOON": {"emoji": "🟡", "label": "SEE DOCTOR SOON", "color": "#FFCC00"},
    "ROUTINE": {"emoji": "🟢", "label": "ROUTINE", "color": "#00CC00"},
    "SELF_CARE": {"emoji": "🔵", "label": "SELF-CARE", "color": "#0099FF"},
    "NEEDS_CLARIFICATION": {
        "emoji": "⚪",
        "label": "MORE INFO NEEDED",
        "color": "#999999",
    },
}


def format_response(ai_response, urgency_info, appointment_info, user_message):
    """
    Formats the final response shown to the user.

    Args:
        ai_response: The raw text from the LLM
        urgency_info: Output from urgency_assessor
        appointment_info: Output from appointment_recommender
        user_message: Original user message

    Returns:
        dict with 'text' (plain text), 'urgency_level', 'urgency_color', and 'metadata'
    """
    urgency_level = urgency_info.get("level", "ROUTINE")
    urgency_display = URGENCY_DISPLAY.get(urgency_level, URGENCY_DISPLAY["ROUTINE"])

    # Build plain text response
    text_parts = []

    # Urgency header
    text_parts.append(f"{urgency_display['emoji']} {urgency_display['label']}")
    text_parts.append("")  # blank line

    # Main AI response
    text_parts.append(ai_response)
    text_parts.append("")

    # Action items section
    text_parts.append("─" * 40)
    text_parts.append("WHAT TO DO NEXT:")
    text_parts.append(
        f"• {urgency_info.get('call_to_action', 'Please consult a healthcare provider')}"
    )

    if appointment_info and urgency_level != "EMERGENCY":
        text_parts.append(
            f"• See a: {appointment_info.get('specialty', 'General Practitioner')}"
        )
        text_parts.append(f"• When: {appointment_info.get('urgency', 'Soon')}")

        if appointment_info.get("what_to_bring"):
            text_parts.append("")
            text_parts.append("Things to bring to your appointment:")
            for item in appointment_info["what_to_bring"]:
                text_parts.append(f"  - {item}")

    # Warning signs
    if urgency_info.get("warning_signs"):
        text_parts.append("")
        text_parts.append("⚠️ Seek IMMEDIATE care if any of these develop:")
        for sign in urgency_info["warning_signs"]:
            text_parts.append(f"  - {sign}")

    # Disclaimer
    text_parts.append("")
    text_parts.append("─" * 40)
    text_parts.append(
        "ℹ️ Disclaimer: NeuroHealth provides general health information only. "
        "Always consult a qualified healthcare professional for medical advice."
    )

    plain_text = "\n".join(text_parts)

    return {
        "text": plain_text,
        "urgency_level": urgency_level,
        "urgency_color": urgency_display["color"],
        "metadata": {
            "urgency": urgency_info,
            "appointment": appointment_info,
        },
    }
