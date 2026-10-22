import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.services.chat_service import ChatService


def test_llm_connection_failure_returns_503_and_records_failure():
    async def run_test():
        with patch(
            "app.services.chat_service.ConversationRepository.get_conversation",
            new_callable=AsyncMock,
            return_value=object(),
        ), patch(
            "app.services.chat_service.MessageRepository.get_messages",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "app.services.chat_service.ConversationHistoryService.format_messages",
            return_value="",
        ), patch(
            "app.services.chat_service.MessageRepository.create_message",
            new_callable=AsyncMock,
        ) as create_message, patch(
            "app.services.chat_service.QueryRewriteService.rewrite",
            return_value="Who approves leave?",
        ), patch(
            "app.services.chat_service.DocumentSearchService.search_with_scores",
            new_callable=AsyncMock,
            return_value=[(object(), 0.1)],
        ), patch(
            "app.services.chat_service.EvidenceSufficiencyService.evaluate",
            return_value=True,
        ), patch(
            "app.services.chat_service.ContextBuilder.build",
            return_value="Retrieved context",
        ), patch(
            "app.services.chat_service.PromptBuilder.build",
            return_value="Generated prompt",
        ), patch(
            "app.services.chat_service.LLMService.generate",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Ollama unavailable"),
        ), patch(
            "app.services.chat_service.logger.exception",
        ) as log_exception:
            with pytest.raises(HTTPException) as exc_info:
                await ChatService.chat(
                    db=None,
                    conversation_id=3,
                    user_id=1,
                    question="Who approves leave?",
                )

        assert exc_info.value.status_code == 503
        assert "temporarily unavailable" in exc_info.value.detail

        assert create_message.await_count == 2
        assert create_message.await_args_list[0].kwargs == {
            "db": None,
            "conversation_id": 3,
            "role": "user",
            "content": "Who approves leave?",
        }

        failure_message = create_message.await_args_list[1].kwargs
        assert failure_message["role"] == "assistant"
        assert "temporarily unavailable" in failure_message["content"]
        assert "Please try again" in failure_message["content"]

        log_exception.assert_called_once()

    asyncio.run(run_test())
