from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

model = CrossEncoder(MODEL_NAME)


question = "Who approves an employee's leave request?"

chunks = [
    "Employees receive 20 days of annual leave.",
    "Managers are responsible for reviewing and approving leave requests.",
    "Employees can contact HR if they have questions about the leave policy.",
]


pairs = [
    (question, chunk)
    for chunk in chunks
]


scores = model.predict(pairs)


print("\n===== RERANKING =====")

for chunk, score in zip(chunks, scores):

    print("\nChunk:")
    print(chunk)

    print(f"Score: {score}")