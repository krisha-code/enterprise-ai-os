from app.services.embedding_service import EmbeddingService


text = "Employees receive 20 days of annual leave."

embedding = EmbeddingService.generate_embedding(
    text
)

print("Embedding dimension:", len(embedding))
print("First 5 values:", embedding[:5])