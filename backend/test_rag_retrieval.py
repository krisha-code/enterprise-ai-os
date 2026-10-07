import asyncio
from statistics import mean

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.hybrid_search_service import HybridSearchService
from app.services.reranker_service import RerankerService
from app.services.evidence_sufficiency_service import (
    EvidenceSufficiencyService,
)


USER_ID = 1
RETRIEVAL_LIMIT = 20


RAG_EVALUATION_QUESTIONS = [
    {
        "id": 1,
        "question": "What is covered in MODULE 1?",
        "answerable": True,
        "expected_sections": ["MODULE 1"],
    },
    {
        "id": 2,
        "question": "What is a fixed-wing UAV?",
        "answerable": True,
        "expected_sections": ["1. Fixed-Wing UAV"],
    },
    {
        "id": 3,
        "question": "What are the advantages of multi-rotor UAVs?",
        "answerable": True,
        "expected_sections": ["2. Multi-Rotor UAV"],
    },
    {
        "id": 4,
        "question": "What are the disadvantages of multi-rotor UAVs?",
        "answerable": True,
        "expected_sections": ["2. Multi-Rotor UAV"],
    },
    {
        "id": 5,
        "question": "What is a single-rotor UAV?",
        "answerable": True,
        "expected_sections": ["3. Single-Rotor UAV"],
    },
    {
        "id": 6,
        "question": "What is a Hybrid VTOL UAV?",
        "answerable": True,
        "expected_sections": ["4. Hybrid VTOL UAV"],
    },
    {
        "id": 7,
        "question": "Compare fixed-wing and multi-rotor UAVs.",
        "answerable": True,
        "expected_sections": [
            "1. Fixed-Wing UAV",
            "2. Multi-Rotor UAV",
        ],
    },
    {
        "id": 8,
        "question": "What agricultural uses are mentioned for multi-rotor UAVs?",
        "answerable": True,
        "expected_sections": ["2. Multi-Rotor UAV"],
    },
    {
        "id": 9,
        "question": "What are the advantages of fixed-wing UAVs?",
        "answerable": True,
        "expected_sections": ["1. Fixed-Wing UAV"],
    },
    {
        "id": 10,
        "question": "What information is provided about underwater drones?",
        "answerable": False,
        "expected_sections": [],
    },
    {
        "id": 11,
        "question": "What are the specifications of underwater drones?",
        "answerable": False,
        "expected_sections": [],
    },
    {
        "id": 12,
        "question": "How are drones used in medical surgery?",
        "answerable": False,
        "expected_sections": [],
    },
    {
        "id": 13,
        "question": "What battery chemistry is used in these UAVs?",
        "answerable": False,
        "expected_sections": [],
    },
    {
        "id": 14,
        "question": "What is the maximum altitude of the UAVs?",
        "answerable": False,
        "expected_sections": [],
    },
    {
        "id": 15,
        "question": "Who manufactures the UAVs described in the document?",
        "answerable": False,
        "expected_sections": [],
    },
]


def calculate_rank_features(
    reranked_results: list[tuple[DocumentChunk, float]],
    expected_sections: list[str],
) -> dict:
    """
    Calculate diagnostic features from reranked results.

    IMPORTANT:

    Production evidence decisions must NOT use
    expected_sections or any other ground-truth information.

    expected_sections is used only by the evaluation harness
    to measure whether known relevant sections were retrieved.
    """

    if not reranked_results:
        return {
            "best_score": None,
            "second_score": None,
            "third_score": None,
            "score_gap": None,
            "count_ge_2": 0,
            "count_ge_4": 0,
            "count_ge_6": 0,
            "average_top_3": None,
            "average_top_5": None,
            "matching_top_5_count": 0,
            "unique_section_count": 0,
            "dominant_section_count": 0,
            "first_relevant_rank": None,
        }

    scores = [
        float(score)
        for _, score in reranked_results
    ]

    best_score = scores[0]

    second_score = (
        scores[1]
        if len(scores) > 1
        else None
    )

    third_score = (
        scores[2]
        if len(scores) > 2
        else None
    )

    score_gap = (
        best_score - second_score
        if second_score is not None
        else None
    )

    count_ge_2 = sum(
        1
        for score in scores
        if score >= 2.0
    )

    count_ge_4 = sum(
        1
        for score in scores
        if score >= 4.0
    )

    count_ge_6 = sum(
        1
        for score in scores
        if score >= 6.0
    )

    top_3_scores = scores[:3]

    top_5_scores = scores[:5]

    average_top_3 = (
        mean(top_3_scores)
        if top_3_scores
        else None
    )

    average_top_5 = (
        mean(top_5_scores)
        if top_5_scores
        else None
    )

    # ---------------------------------------------------------
    # Evaluation-only ground-truth diagnostic
    # ---------------------------------------------------------

    matching_top_5_count = 0
    first_relevant_rank = None

    for rank, (chunk, _) in enumerate(
        reranked_results[:5],
        start=1,
    ):
        if (
            chunk.section_title
            and chunk.section_title in expected_sections
        ):
            matching_top_5_count += 1

            if first_relevant_rank is None:
                first_relevant_rank = rank

    # ---------------------------------------------------------
    # Section distribution
    # ---------------------------------------------------------

    sections = [
        chunk.section_title
        for chunk, _ in reranked_results[:5]
        if chunk.section_title
    ]

    unique_section_count = len(set(sections))

    dominant_section_count = 0

    if sections:
        section_counts = {}

        for section in sections:
            section_counts[section] = (
                section_counts.get(section, 0) + 1
            )

        dominant_section_count = max(
            section_counts.values()
        )

    return {
        "best_score": best_score,
        "second_score": second_score,
        "third_score": third_score,
        "score_gap": score_gap,
        "count_ge_2": count_ge_2,
        "count_ge_4": count_ge_4,
        "count_ge_6": count_ge_6,
        "average_top_3": average_top_3,
        "average_top_5": average_top_5,
        "matching_top_5_count": matching_top_5_count,
        "unique_section_count": unique_section_count,
        "dominant_section_count": dominant_section_count,
        "first_relevant_rank": first_relevant_rank,
    }


async def evaluate_question(question_data: dict):
    question_id = question_data["id"]
    question = question_data["question"]
    answerable = question_data["answerable"]
    expected_sections = question_data["expected_sections"]

    async with AsyncSessionLocal() as db:

        # -----------------------------------------------------
        # Step 1: Hybrid retrieval
        # -----------------------------------------------------

        hybrid_results = await HybridSearchService.search(
            db=db,
            query=question,
            user_id=USER_ID,
            limit=RETRIEVAL_LIMIT,
            max_distance=None,
        )

        if not hybrid_results:
            print(
                f"\nQ{question_id} | "
                f"answerable={answerable} | "
                f"NO RETRIEVAL RESULTS"
            )

            return {
                "question_id": question_id,
                "answerable": answerable,
                "evidence_sufficient": False,
                "first_relevant_rank": None,
            }

        # -----------------------------------------------------
        # Step 2: Extract chunks
        # -----------------------------------------------------

        chunks = [
            chunk
            for chunk, _ in hybrid_results
        ]

        # -----------------------------------------------------
        # Step 3: Rerank
        # -----------------------------------------------------

        reranked_results = RerankerService.rerank(
            question=question,
            chunks=chunks,
        )

        # -----------------------------------------------------
        # Step 4: Calculate diagnostic features
        # -----------------------------------------------------

        features = calculate_rank_features(
            reranked_results=reranked_results,
            expected_sections=expected_sections,
        )

        # -----------------------------------------------------
        # Step 5: Production evidence decision
        #
        # IMPORTANT:
        # This uses the production service.
        # No expected sections or ground truth are passed here.
        # -----------------------------------------------------

        evidence_sufficient = (
            EvidenceSufficiencyService.is_sufficient(
                best_score=features["best_score"],
                average_top_3=features["average_top_3"],
                count_ge_2=features["count_ge_2"],
                dominant_section_count=features[
                    "dominant_section_count"
                ],
            )
        )

        # -----------------------------------------------------
        # Print question
        # -----------------------------------------------------

        print("\n" + "=" * 80)

        print(
            f"QUESTION {question_id}: "
            f"{question}"
        )

        print(
            f"answerable={answerable}"
        )

        print("=" * 80)

        # -----------------------------------------------------
        # Print top results
        # -----------------------------------------------------

        for rank, (chunk, score) in enumerate(
            reranked_results[:5],
            start=1,
        ):
            section = (
                chunk.section_title
                if chunk.section_title
                else "Unknown section"
            )

            print(
                f"RANK {rank} | "
                f"score={float(score):.4f} | "
                f"chunk_id={chunk.id} | "
                f"section={section}"
            )

        # -----------------------------------------------------
        # Feature summary
        # -----------------------------------------------------

        print("\nEVIDENCE FEATURE SUMMARY")

        print(
            f"Q{question_id} | "
            f"answerable={answerable} | "
            f"best={features['best_score']:.4f} | "
            f"gap={features['score_gap']:.4f} | "
            f">=2:{features['count_ge_2']} | "
            f">=4:{features['count_ge_4']} | "
            f">=6:{features['count_ge_6']} | "
            f"avg3={features['average_top_3']:.4f} | "
            f"avg5={features['average_top_5']:.4f} | "
            f"expected_top5={features['matching_top_5_count']} | "
            f"unique_sections={features['unique_section_count']} | "
            f"dominant_section={features['dominant_section_count']} | "
            f"first_rank={features['first_relevant_rank']} | "
            f"evidence_sufficient={evidence_sufficient}"
        )

        return {
            "question_id": question_id,
            "answerable": answerable,
            "evidence_sufficient": evidence_sufficient,
            "features": features,
        }


async def main():
    results = []

    for question_data in RAG_EVALUATION_QUESTIONS:
        result = await evaluate_question(
            question_data
        )

        results.append(result)

    # ---------------------------------------------------------
    # Classification summary
    # ---------------------------------------------------------

    true_positive = 0
    false_negative = 0
    true_negative = 0
    false_positive = 0

    for result in results:

        actual = result["answerable"]
        predicted = result["evidence_sufficient"]

        if actual and predicted:
            true_positive += 1

        elif actual and not predicted:
            false_negative += 1

        elif not actual and not predicted:
            true_negative += 1

        elif not actual and predicted:
            false_positive += 1

    print("\n")
    print("=" * 80)
    print("EVIDENCE SUFFICIENCY CLASSIFICATION")
    print("=" * 80)

    print(
        f"TRUE_POSITIVE={true_positive}"
    )

    print(
        f"FALSE_NEGATIVE={false_negative}"
    )

    print(
        f"TRUE_NEGATIVE={true_negative}"
    )

    print(
        f"FALSE_POSITIVE={false_positive}"
    )

    print(
        f"TOTAL_QUESTIONS={len(results)}"
    )


if __name__ == "__main__":
    asyncio.run(main())