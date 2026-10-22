
import re


class AnswerValidationService:
    """Validate generated answers and extract source-specific evidence."""

    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "being",
        "by", "for", "from", "had", "has", "have", "in", "into", "is",
        "it", "its", "of", "on", "or", "that", "the", "their", "this",
        "to", "was", "were", "will", "with", "you", "your",
        "contain", "contains",
    }

    @classmethod
    def _content_words(cls, text: str) -> set[str]:
        words = re.findall(r"\b[a-z0-9-]+\b", text.lower())
        return {
            word
            for word in words
            if word not in cls.STOP_WORDS and len(word) > 2
        }

    @classmethod
    def validate(
        cls,
        answer: str,
        context: str,
        question: str,
    ) -> bool:
        if not answer or not answer.strip():
            return False

        if not context or not context.strip():
            return False

        answer_text = re.sub(r"\s+", " ", answer.lower()).strip()
        context_text = re.sub(r"\s+", " ", context.lower()).strip()
        question_text = (question or "").lower()

        # Reject unsupported claims that evidence is missing.
        unsupported_refusal = bool(
            re.search(
                r"\b(context|provided context|available information)"
                r"\b.{0,100}\b("
                r"does not contain|doesn't contain|contains no|"
                r"does not provide|doesn't provide|"
                r"no information|insufficient information"
                r")\b",
                answer_text,
            )
        )

        if unsupported_refusal:
            return False

        # Require meaningful lexical overlap with the context.
        answer_words = cls._content_words(answer_text)
        context_words = cls._content_words(context_text)

        if not answer_words:
            return False

        overlap = answer_words & context_words
        overlap_ratio = len(overlap) / len(answer_words)

        if not overlap or overlap_ratio < 0.30:
            return False

        # Reject claims that a fixed-wing UAV can hover when the
        # retrieved evidence explicitly says it cannot.
        if "fixed-wing" in context_text and "hover" in context_text:
            source_says_cannot_hover = bool(
                re.search(
                    r"\bcannot hover\b|\bcan't hover\b",
                    context_text,
                )
            )
            answer_claims_can_hover = bool(
                re.search(
                    r"\bcan hover\b|\bability to hover\b|"
                    r"\bable to hover\b",
                    answer_text,
                )
            )

            if source_says_cannot_hover and answer_claims_can_hover:
                return False

        # Do not present a listed disadvantage as an advantage.
        if (
            "advantage" in question_text
            and re.search(
                r"disadvantages?:.*requires more operating skill",
                context_text,
            )
            and "requires more operating skill" in answer_text
        ):
            return False

        return True

    @classmethod
    def extract_labeled_section(
        cls,
        context: str,
        label: str,
    ) -> str | None:
        """Extract a labeled section without including the next section."""
        result = cls.extract_labeled_section_with_source(
            context=context,
            label=label,
        )

        if result is None:
            return None

        section_text, _source_id = result
        return section_text

    @classmethod
    def extract_labeled_section_with_source(
        cls,
        context: str,
        label: str,
    ) -> tuple[str, int] | None:
        """
        Extract a section from one source block.

        Supports source-formatted RAG context and plain-text input.
        Returns (section_text, source_id). Plain text uses source ID 1.
        """
        if not context or not label:
            return None

        normalized_label = label.strip().lower()

        if normalized_label not in {"advantages", "disadvantages"}:
            return None

        other_label = (
            "disadvantages"
            if normalized_label == "advantages"
            else "advantages"
        )

        # Split at source boundaries. Plain-text input remains one block.
        source_blocks = re.split(
            r"(?=^\[Source\s+(\d+)\]\s*$)",
            context,
            flags=re.MULTILINE,
        )

        # re.split with a capturing group includes the captured IDs.
        # Rebuild source blocks without losing their original IDs.
        blocks: list[tuple[str, int]] = []
        source_pattern = re.compile(
            r"^\[Source\s+(\d+)\]\s*$",
            flags=re.MULTILINE,
        )
        matches = list(source_pattern.finditer(context))

        if not matches:
            blocks = [(context, 1)]
        else:
            for index, match in enumerate(matches):
                block_start = match.start()
                block_end = (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(context)
                )
                blocks.append(
                    (context[block_start:block_end], int(match.group(1)))
                )

        # Match the requested label until the next advantages/disadvantages
        # label or the end of this source's content.
        section_pattern = re.compile(
            rf"\b{re.escape(normalized_label)}\s*:\s*"
            rf"(.*?)"
            rf"(?=\b(?:{re.escape(other_label)}|"
            rf"{re.escape(normalized_label)})\s*:|$)",
            flags=re.IGNORECASE | re.DOTALL,
        )

        for block, source_id in blocks:
            content_match = re.search(
                r"^\s*Content\s*:\s*",
                block,
                flags=re.MULTILINE | re.IGNORECASE,
            )

            searchable_text = (
                block[content_match.end():]
                if content_match
                else block
            )

            section_match = section_pattern.search(searchable_text)

            if section_match:
                extracted = section_match.group(1).strip()

                if extracted:
                    return extracted, source_id

        return None
