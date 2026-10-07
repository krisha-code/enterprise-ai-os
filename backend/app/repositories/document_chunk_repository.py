from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:

    @staticmethod
    async def create_many(
        db: AsyncSession,
        document_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
        section_titles: list[str | None] | None = None,
        page_numbers: list[int | None] | None = None,
    ) -> list[DocumentChunk]:

        document_chunks = []

        for index, content in enumerate(chunks):
            section_title = (
                section_titles[index]
                if section_titles is not None
                else None
            )

            page_number = (
                page_numbers[index]
                if page_numbers is not None
                else None
            )

            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
                embedding=embeddings[index],
                section_title=section_title,
                page_number=page_number,
            )

            document_chunks.append(document_chunk)

        db.add_all(document_chunks)
        await db.commit()

        return document_chunks

    @staticmethod
    async def similarity_search(
        db: AsyncSession,
        query_embedding: list[float],
        user_id: int,
        limit: int = 5,
    ) -> list[DocumentChunk]:

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        result = await db.execute(
            select(DocumentChunk)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.user_id == user_id,
                Document.is_active.is_(True),
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(limit)
        )

        return list(result.scalars().all())

    @staticmethod
    async def similarity_search_with_scores(
        db: AsyncSession,
        query_embedding: list[float],
        user_id: int,
        limit: int = 5,
        max_distance: float | None = None,
    ):

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        query = (
            select(
                DocumentChunk,
                distance.label("distance"),
            )
            .options(
                selectinload(DocumentChunk.document)
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.user_id == user_id,
                Document.is_active.is_(True),
                DocumentChunk.embedding.is_not(None),
            )
        )

        if max_distance is not None:
            query = query.where(
                distance <= max_distance
            )

        query = (
            query
            .order_by(distance)
            .limit(limit)
        )

        result = await db.execute(query)

        return result.all()

    @staticmethod
    async def keyword_search(
        db: AsyncSession,
        query_text: str,
        user_id: int,
        limit: int = 5,
    ):

        search_text = func.concat(
            func.coalesce(
                DocumentChunk.section_title,
                "",
            ),
            " ",
            DocumentChunk.content,
        )

        search_vector = func.to_tsvector(
            "english",
            search_text,
        )

        search_query = func.plainto_tsquery(
            "english",
            query_text,
        )

        rank = func.ts_rank(
            search_vector,
            search_query,
        )

        result = await db.execute(
            select(
                DocumentChunk,
                rank.label("rank"),
            )
            .options(
                selectinload(DocumentChunk.document)
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.user_id == user_id,
                Document.is_active.is_(True),
                search_vector.op("@@")(search_query),
            )
            .order_by(rank.desc())
            .limit(limit)
        )

        return result.all()