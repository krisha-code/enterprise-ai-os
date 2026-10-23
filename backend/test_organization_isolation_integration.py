import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.database.session import AsyncSessionLocal, engine
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.organization import Organization
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository


def test_documents_and_search_results_are_isolated_between_organizations():
    async def run_test():
        # Async tests in this suite use separate asyncio.run() event loops.
        # Dispose pooled asyncpg connections before opening one in this loop.
        await engine.dispose()

        async with AsyncSessionLocal() as db:
            try:
                existing_user = await db.scalar(select(User).limit(1))
                assert existing_user is not None, "Seed at least one user first"

                marker = uuid4().hex
                other_org = Organization(name=f"Isolation Test {marker}")
                db.add(other_org)
                await db.flush()

                other_user = User(
                    name="Temporary Isolation Test User",
                    email=f"org-isolation-{marker}@example.test",
                    password_hash="not-used-by-this-test",
                    role_id=existing_user.role_id,
                    organization_id=other_org.id,
                )
                db.add(other_user)
                await db.flush()

                document = Document(
                    user_id=other_user.id,
                    organization_id=other_org.id,
                    filename=f"isolation-{marker}.txt",
                    file_path=f"test-only/{marker}.txt",
                    content_type="text/plain",
                    is_active=True,
                    processing_status="completed",
                )
                db.add(document)
                await db.flush()

                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=0,
                    content=f"uniqueisolation{marker} company privacy probe",
                    section_title="Isolation test",
                    embedding=[0.1] * 384,
                )
                db.add(chunk)
                await db.flush()

                existing_org_documents = await DocumentRepository.get_by_user(
                    db,
                    existing_user.organization_id,
                )
                other_org_documents = await DocumentRepository.get_by_user(
                    db,
                    other_org.id,
                )
                assert document.id not in {item.id for item in existing_org_documents}
                assert document.id in {item.id for item in other_org_documents}

                existing_org_keywords = await DocumentChunkRepository.keyword_search(
                    db,
                    query_text=f"uniqueisolation{marker}",
                    organization_id=existing_user.organization_id,
                )
                other_org_keywords = await DocumentChunkRepository.keyword_search(
                    db,
                    query_text=f"uniqueisolation{marker}",
                    organization_id=other_org.id,
                )
                assert chunk.id not in {item.id for item, _ in existing_org_keywords}
                assert chunk.id in {item.id for item, _ in other_org_keywords}

                existing_org_vectors = await DocumentChunkRepository.similarity_search_with_scores(
                    db,
                    query_embedding=[0.1] * 384,
                    organization_id=existing_user.organization_id,
                )
                other_org_vectors = await DocumentChunkRepository.similarity_search_with_scores(
                    db,
                    query_embedding=[0.1] * 384,
                    organization_id=other_org.id,
                )
                assert chunk.id not in {item.id for item, _ in existing_org_vectors}
                assert chunk.id in {item.id for item, _ in other_org_vectors}
            finally:
                # The test uses the configured DB but leaves no test records behind.
                await db.rollback()

    asyncio.run(run_test())
