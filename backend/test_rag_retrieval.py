
import asyncio
from statistics import mean

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.document_search_service import DocumentSearchService
from app.services.evidence_sufficiency_service import (
    EvidenceSufficiencyService,
)


ORGANIZATION_ID = 1

# Match the production search call: retrieve and rank up to 20 results.
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
        "question": (
            "What agricultural uses are mentioned for multi-rotor UAVs?"
        ),
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
        "question": (
            "Who manufactures the UAVs described in the document?"
        ),
        "answerable": False,
        "expected_sections": [],
    },
]


def calculate_rank_features(
    ranked_results: list[tuple[DocumentChunk, float]],
    expected_sections: list[str],
) -> dict:
    """
    Calculate ranking diagnostics and retrieval completeness.

    Expected section names are used only to measure retrieval
    completeness. They are never passed to the evidence decision.
    """

    if not ranked_results:
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
            "matched_expected_section_count": 0,
            "unique_section_count": 0,
            "dominant_section_count": 0,
            "first_relevant_rank": None,
        }

    # Search results are already ordered by the production reranker.
    top_5_results = ranked_results[:5]
    top_5_scores = [
        float(score) for _, score in top_5_results
    ]
    top_3_scores = top_5_scores[:3]

    # Calculate the top scores and their separation.
    sorted_top_5_scores = sorted(
        top_5_scores,
        reverse=True,
    )

    best_score = sorted_top_5_scores[0]

    second_score = (
        sorted_top_5_scores[1]
        if len(sorted_top_5_scores) > 1
        else None
    )

    third_score = (
        sorted_top_5_scores[2]
        if len(sorted_top_5_scores) > 2
        else None
    )

    score_gap = (
        best_score - second_score
        if second_score is not None
        else None
    )

    # Normalize expected section names for comparison.
    normalized_expected = [
        section.strip().casefold()
        for section in expected_sections
        if section.strip()
    ]

    matching_top_5_count = 0
    matched_expected_sections = set()
    first_relevant_rank = None

    for rank, (chunk, _) in enumerate(
        top_5_results,
        start=1,
    ):
        section_title = (
            chunk.section_title.strip().casefold()
            if chunk.section_title
            else ""
        )

        matched_here = [
            expected
            for expected in normalized_expected
            if expected in section_title
        ]

        if matched_here:
            matching_top_5_count += 1
            matched_expected_sections.update(matched_here)

            if first_relevant_rank is None:
                first_relevant_rank = rank

    # Calculate section concentration among the top five.
    sections = [
        chunk.section_title
        for chunk, _ in top_5_results
        if chunk.section_title
    ]

    section_counts = {}

    for section in sections:
        section_counts[section] = (
            section_counts.get(section, 0) + 1
        )

    unique_section_count = len(set(sections))

    dominant_section_count = (
        max(section_counts.values())
        if section_counts
        else 0
    )

    return {
        "best_score": best_score,
        "second_score": second_score,
        "third_score": third_score,
        "score_gap": score_gap,
        "count_ge_2": sum(
            score >= 2.0 for score in top_5_scores
        ),
        "count_ge_4": sum(
            score >= 4.0 for score in top_5_scores
        ),
        "count_ge_6": sum(
            score >= 6.0 for score in top_5_scores
        ),
        "average_top_3": (
            mean(top_3_scores) if top_3_scores else None
        ),
        "average_top_5": (
            mean(top_5_scores) if top_5_scores else None
        ),
        "matching_top_5_count": matching_top_5_count,
        "matched_expected_section_count": len(
            matched_expected_sections
        ),
        "unique_section_count": unique_section_count,
        "dominant_section_count": dominant_section_count,
        "first_relevant_rank": first_relevant_rank,
    }


async def evaluate_question(question_data: dict) -> dict:
    question_id = question_data["id"]
    question = question_data["question"]
    answerable = question_data["answerable"]
    expected_sections = question_data["expected_sections"]

    async with AsyncSessionLocal() as db:
        # Use the same search service as production ChatService.
        ranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=question,
                organization_id=ORGANIZATION_ID,
                limit=RETRIEVAL_LIMIT,
                max_distance=None,
            )
        )

    if not ranked_results:
        print("\n" + "=" * 80)
        print(f"QUESTION {question_id}: {question}")
        print("NO RETRIEVAL RESULTS")
        print("=" * 80)

        retrieval_complete = len(expected_sections) == 0

        return {
            "question_id": question_id,
            "answerable": answerable,
            "evidence_sufficient": False,
            "retrieval_complete": retrieval_complete,
            "features": calculate_rank_features(
                [],
                expected_sections,
            ),
        }

    features = calculate_rank_features(
        ranked_results=ranked_results,
        expected_sections=expected_sections,
    )

    expected_section_count = len({
        section.strip().casefold()
        for section in expected_sections
        if section.strip()
    })

    found_section_count = features[
        "matched_expected_section_count"
    ]

    retrieval_complete = (
        found_section_count == expected_section_count
    )

    if answerable and not retrieval_complete:
        print(
            f"\nRETRIEVAL INCOMPLETE | Q{question_id} | "
            f"expected={expected_section_count} | "
            f"found={found_section_count}"
        )

    # Apply the same evidence-sufficiency rules as production.
    # The score gap is passed to support the new Rule 2B.
    # Expected sections are not used in this decision.
    evidence_sufficient = (
        EvidenceSufficiencyService.is_sufficient(
            best_score=features["best_score"],
            average_top_3=features["average_top_3"],
            count_ge_2=features["count_ge_2"],
            dominant_section_count=features[
                "dominant_section_count"
            ],
            score_gap=features["score_gap"],
        )
    )

    print("\n" + "=" * 80)
    print(f"QUESTION {question_id}: {question}")
    print(f"answerable={answerable}")
    print("=" * 80)

    for rank, (chunk, score) in enumerate(
        ranked_results[:5],
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

    print("\nEVIDENCE FEATURE SUMMARY")

    best = features["best_score"]
    gap = features["score_gap"]
    avg3 = features["average_top_3"]
    avg5 = features["average_top_5"]

    gap_text = (
        f"{gap:.4f}" if gap is not None else "N/A"
    )
    avg3_text = (
        f"{avg3:.4f}" if avg3 is not None else "N/A"
    )
    avg5_text = (
        f"{avg5:.4f}" if avg5 is not None else "N/A"
    )

    print(
        f"Q{question_id} | "
        f"answerable={answerable} | "
        f"best={best:.4f} | "
        f"gap={gap_text}"
    )

    print(
        f">=2:{features['count_ge_2']} | "
        f">=4:{features['count_ge_4']} | "
        f">=6:{features['count_ge_6']} | "
        f"avg3={avg3_text} | "
        f"avg5={avg5_text} | "
        f"expected_top5={features['matching_top_5_count']} | "
        f"expected_sections_found="
        f"{features['matched_expected_section_count']} | "
        f"unique_sections={features['unique_section_count']} | "
        f"dominant_section={features['dominant_section_count']} | "
        f"first_rank={features['first_relevant_rank']} | "
        f"evidence_sufficient={evidence_sufficient} | "
        f"retrieval_complete={retrieval_complete}"
    )

    return {
        "question_id": question_id,
        "answerable": answerable,
        "evidence_sufficient": evidence_sufficient,
        "retrieval_complete": retrieval_complete,
        "features": features,
    }


async def main():
    results = []

    for question_data in RAG_EVALUATION_QUESTIONS:
        result = await evaluate_question(question_data)
        results.append(result)

    true_positive = 0
    false_negative = 0
    true_negative = 0
    false_positive = 0

    complete_answerable = 0
    incomplete_answerable = 0

    for result in results:
        actual = result["answerable"]
        predicted = result["evidence_sufficient"]

        if actual and predicted:
            true_positive += 1
        elif actual and not predicted:
            false_negative += 1
        elif not actual and not predicted:
            true_negative += 1
        else:
            false_positive += 1

        if actual:
            if result["retrieval_complete"]:
                complete_answerable += 1
            else:
                incomplete_answerable += 1

    print("\n")
    print("=" * 80)
    print("EVIDENCE SUFFICIENCY CLASSIFICATION")
    print("=" * 80)
    print(f"TRUE_POSITIVE={true_positive}")
    print(f"FALSE_NEGATIVE={false_negative}")
    print(f"TRUE_NEGATIVE={true_negative}")
    print(f"FALSE_POSITIVE={false_positive}")
    print(f"TOTAL_QUESTIONS={len(results)}")

    print("\n")
    print("=" * 80)
    print("RETRIEVAL COMPLETENESS SUMMARY")
    print("=" * 80)
    print(
        "ANSWERABLE_WITH_COMPLETE_RETRIEVAL="
        f"{complete_answerable}"
    )
    print(
        "ANSWERABLE_WITH_INCOMPLETE_RETRIEVAL="
        f"{incomplete_answerable}"
    )


if __name__ == "__main__":
    asyncio.run(main())
