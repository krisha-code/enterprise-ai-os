import asyncio

import pytest

from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)


def test_create_many_adds_all_chunks_without_committing():
    async def run_test():
        added_objects = []
        flush_calls = []

        class FakeDB:
            def add_all(self, objects):
                added_objects.extend(objects)

            async def flush(self):
                flush_calls.append(True)

        db = FakeDB()

        chunks = await DocumentChunkRepository.create_many(
            db=db,
            document_id=42,
            chunks=["First chunk", "Second chunk", "Third chunk"],
            embeddings=[
                [0.1] * 384,
                [0.2] * 384,
                [0.3] * 384,
            ],
            section_titles=["Intro", "Policy", "Summary"],
            page_numbers=[1, 2, 3],
        )

        assert len(chunks) == 3
        assert len(added_objects) == 3
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
        assert [chunk.content for chunk in chunks] == [
            "First chunk",
            "Second chunk",
            "Third chunk",
        ]
        assert [chunk.section_title for chunk in chunks] == [
            "Intro",
            "Policy",
            "Summary",
        ]
        assert [chunk.page_number for chunk in chunks] == [1, 2, 3]
        assert flush_calls == [True]

    asyncio.run(run_test())


def test_create_many_rejects_mismatched_embedding_count():
    async def run_test():
        class FakeDB:
            def add_all(self, objects):
                raise AssertionError("Should not add mismatched chunks")

            async def flush(self):
                raise AssertionError("Should not flush mismatched chunks")

        with pytest.raises(
            ValueError,
            match="Chunk count does not match embedding count",
        ):
            await DocumentChunkRepository.create_many(
                db=FakeDB(),
                document_id=42,
                chunks=["First chunk", "Second chunk"],
                embeddings=[[0.1] * 384],
            )

    asyncio.run(run_test())


def test_create_many_rejects_mismatched_metadata():
    async def run_test():
        class FakeDB:
            def add_all(self, objects):
                raise AssertionError("Should not add mismatched chunks")

            async def flush(self):
                raise AssertionError("Should not flush mismatched chunks")

        with pytest.raises(
            ValueError,
            match="Chunk count does not match section-title count",
        ):
            await DocumentChunkRepository.create_many(
                db=FakeDB(),
                document_id=42,
                chunks=["First chunk", "Second chunk"],
                embeddings=[
                    [0.1] * 384,
                    [0.2] * 384,
                ],
                section_titles=["Intro"],
            )

    asyncio.run(run_test())


def test_delete_by_document_flushes_delete():
    async def run_test():
        executed_statements = []
        flush_calls = []

        class FakeDB:
            async def execute(self, statement):
                executed_statements.append(statement)

            async def flush(self):
                flush_calls.append(True)

        db = FakeDB()

        await DocumentChunkRepository.delete_by_document(
            db=db,
            document_id=42,
        )

        assert len(executed_statements) == 1
        assert flush_calls == [True]

    asyncio.run(run_test())