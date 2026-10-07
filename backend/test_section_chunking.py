from pathlib import Path

from app.services.document_text_extractor import DocumentTextExtractor
from app.services.document_chunker import DocumentChunker


Q1_PATH = Path("uploads/documents/debcb675-2832-4f47-8a1d-b7c26c3c7808.docx")

blocks = DocumentTextExtractor.extract(
    file_path=str(Q1_PATH),
    content_type=(
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    ),
)

chunks = DocumentChunker.chunk_text(blocks)

print(f"Extracted blocks: {len(blocks)}")
print(f"Generated chunks: {len(chunks)}")
print()

for index, chunk in enumerate(chunks):
    if chunk.section_title in {
        "1. Fixed-Wing UAV",
        "2. Multi-Rotor UAV",
        "3. Single-Rotor UAV",
    }:
        print("=" * 80)
        print(f"CHUNK {index}")
        print(f"SECTION: {chunk.section_title}")
        print(f"CONTENT: {chunk.content[:500]}")
        print()