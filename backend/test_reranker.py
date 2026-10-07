from app.services.reranker_service import (
    RerankerService,
)


question = "Who approves an employee's leave request?"


chunks = [
    "Employees receive 20 days of annual leave.",
    "Managers are responsible for reviewing and approving leave requests.",
    "Employees can contact HR if they have questions about the leave policy.",
]


print("===== RERANKING =====")

results = []

for chunk in chunks:

    score = RerankerService.score(
        question=question,
        chunk=chunk,
    )

    results.append(
        (chunk, score)
    )


results.sort(
    key=lambda item: item[1],
    reverse=True,
)


for rank, (chunk, score) in enumerate(
    results,
    start=1,
):

    print(f"\nRank {rank}")
    print(f"Score: {score}")
    print(f"Content: {chunk}")