def rrf_score(rank: int, k: int = 60) -> float:
    return 1 / (k + rank)


vector_results = {
    "chunk_a": 1,
    "chunk_b": 2,
    "chunk_c": 3,
}

keyword_results = {
    "chunk_b": 1,
    "chunk_a": 2,
    "chunk_d": 3,
}


scores = {}


for chunk_id, rank in vector_results.items():
    scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score(rank)


for chunk_id, rank in keyword_results.items():
    scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score(rank)


final_results = sorted(
    scores.items(),
    key=lambda item: item[1],
    reverse=True,
)


print("===== HYBRID RESULTS =====")

for rank, (chunk_id, score) in enumerate(
    final_results,
    start=1,
):
    print(
        f"Rank {rank}: "
        f"{chunk_id} "
        f"→ {score:.6f}"
    )