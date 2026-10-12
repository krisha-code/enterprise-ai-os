
import re


class QueryRewriteService:
    """Rule-based rewriting for common UAV follow-up questions."""

    UAV_TYPES = (
        "multi-rotor UAV",
        "fixed-wing UAV",
        "single-rotor UAV",
        "hybrid VTOL UAV",
    )

    FOLLOW_UP_PATTERNS = (
        (
            r"what are its advantages\??",
            "advantages",
            False,
        ),
        (
            r"what are its disadvantages\??",
            "disadvantages",
            False,
        ),
        (
            r"what are their advantages\??",
            "advantages",
            True,
        ),
        (
            r"what are their disadvantages\??",
            "disadvantages",
            True,
        ),
        (
            r"what is it\??",
            "definition",
            False,
        ),
    )

    @staticmethod
    def rewrite(
        question: str,
        conversation_history: str,
    ) -> str:
        question = question.strip()

        if not question or not conversation_history.strip():
            return question

        if conversation_history.strip().lower() == "no previous conversation.":
            return question

        # Find the most recently mentioned supported UAV type.
        history_lower = conversation_history.lower()
        mentions = []

        for uav_type in QueryRewriteService.UAV_TYPES:
            position = history_lower.rfind(uav_type.lower())

            if position >= 0:
                mentions.append((position, uav_type))

        if not mentions:
            return question

        _, uav_type = max(mentions, key=lambda item: item[0])

        # Rewrite only follow-up questions we explicitly understand.
        for pattern, topic, plural in QueryRewriteService.FOLLOW_UP_PATTERNS:
            if re.fullmatch(pattern, question, flags=re.IGNORECASE):
                if topic == "definition":
                    return f"What is a {uav_type}?"

                subject = f"{uav_type}s" if plural else uav_type
                return f"What are the {topic} of {subject}?"

        # Leave all other questions unchanged.
        return question
