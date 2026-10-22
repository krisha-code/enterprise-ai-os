import asyncio

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value


class FakeDB:
    def __init__(self, result):
        self.result = result
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return self.result


def test_get_by_id_and_user_returns_owned_document():
    async def run_test():
        document = Document(
            id=10,
            user_id=7,
            filename="policy.pdf",
            file_path="uploads/policy.pdf",
            content_type="application/pdf",
            is_active=True,
            processing_status="completed",
        )
        db = FakeDB(FakeResult(document))

        result = await DocumentRepository.get_by_id_and_user(
            db=db,
            document_id=10,
            user_id=7,
        )

        assert result is document
        assert len(db.statements) == 1

        sql = str(db.statements[0])
        assert "documents.id" in sql
        assert "documents.user_id" in sql
        assert "documents.is_active" in sql

    asyncio.run(run_test())


def test_get_by_id_and_user_returns_none_when_not_owned():
    async def run_test():
        db = FakeDB(FakeResult(None))

        result = await DocumentRepository.get_by_id_and_user(
            db=db,
            document_id=10,
            user_id=99,
        )

        assert result is None

        sql = str(db.statements[0])
        assert "documents.id" in sql
        assert "documents.user_id" in sql
        assert "documents.is_active" in sql

    asyncio.run(run_test())


def test_get_by_user_filters_inactive_documents():
    async def run_test():
        db = FakeDB(FakeResult([]))

        result = await DocumentRepository.get_by_user(
            db=db,
            user_id=7,
        )

        assert result == []

        sql = str(db.statements[0])
        assert "documents.user_id" in sql
        assert "documents.is_active" in sql

    asyncio.run(run_test())