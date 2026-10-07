from app.services.document_chunker import DocumentChunker


text = """
Transportation Policy

Employees receive a monthly transportation allowance.

Employees can use the allowance for approved commuting expenses.

Leave Policy

Employees receive 20 days of annual leave every year.

Employees must submit leave requests to their manager.
""".strip()


chunks = DocumentChunker.chunk_text(
    text=text,
    chunk_size=120,
    overlap_sentences=1,
)

for index, chunk in enumerate(chunks, start=1):
    print(f"\n===== CHUNK {index} =====")
    print(f"Content: {chunk.content}")
    print(f"Section: {chunk.section_title}")
    print(f"Page: {chunk.page_number}")