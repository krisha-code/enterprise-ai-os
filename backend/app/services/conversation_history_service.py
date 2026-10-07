from app.models.message import Message


class ConversationHistoryService:

    @staticmethod
    def format_messages(
        messages: list[Message],
    ) -> str:
        if not messages:
            return "No previous conversation."

        history_parts = []

        for message in messages:
            role = message.role.capitalize()

            history_parts.append(
                f"{role}: {message.content}"
            )

        return "\n".join(history_parts)