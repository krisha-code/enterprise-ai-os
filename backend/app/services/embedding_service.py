from sentence_transformers import SentenceTransformer


class EmbeddingService:

    MODEL_NAME = "all-MiniLM-L6-v2"

    _model = SentenceTransformer(
        MODEL_NAME
    )

    @classmethod
    def generate_embedding(
        cls,
        text: str,
    ) -> list[float]:

        embedding = cls._model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    @classmethod
    def generate_embeddings(
        cls,
        texts: list[str],
    ) -> list[list[float]]:

        embeddings = cls._model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()