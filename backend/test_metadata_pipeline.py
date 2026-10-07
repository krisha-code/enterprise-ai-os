import asyncio

from app.services.document_chunker import DocumentChunker
from app.services.document_text_extractor import DocumentTextExtractor


async def main():

    file_path = (
        "uploads/documents/"
        "fb563b86-579e-4c25-b0c6-5736a8ba492f.docx"
    )

    content_type = (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    )

    # ----------------------------------------
    # Extract
    # ----------------------------------------

    extracted_blocks = DocumentTextExtractor.extract(
        file_path=file_path,
        content_type=content_type,
    )

    print("\n--- EXTRACTED BLOCKS ---")

    for index, block in enumerate(extracted_blocks[:10]):

        print(f"\nBlock {index + 1}")
        print(f"Content: {block.content[:120]}")
        print(f"Section: {block.section_title}")
        print(f"Page: {block.page_number}")

    # ----------------------------------------
    # Chunk
    # ----------------------------------------

    chunks = DocumentChunker.chunk_text(
        extracted_blocks
    )

    print("\n")
    print("=" * 60)
    print(f"Final chunks: {len(chunks)}")

    # ----------------------------------------
    # Display chunks
    # ----------------------------------------

    for index, chunk in enumerate(chunks[:10]):

        print("\n" + "-" * 60)

        print(f"Chunk: {index}")
        print(f"Page: {chunk.page_number}")
        print(f"Section: {chunk.section_title}")
        print(f"Content: {chunk.content[:200]}")


if __name__ == "__main__":
    asyncio.run(main())