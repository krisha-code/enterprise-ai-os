import importlib.util
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).with_name("test_rag_retrieval.py")

spec = importlib.util.spec_from_file_location(
    "rag_retrieval_diagnostic",
    MODULE_PATH,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

calculate_rank_features = module.calculate_rank_features


def make_result(section, score):
    chunk = SimpleNamespace(section_title=section)
    return chunk, score


def test_empty_results_return_empty_feature_defaults():
    features = calculate_rank_features([], ["Section A"])

    assert features["best_score"] is None
    assert features["score_gap"] is None
    assert features["matching_top_5_count"] == 0
    assert features["matched_expected_section_count"] == 0
    assert features["first_relevant_rank"] is None


def test_scores_and_expected_sections_are_calculated():
    results = [
        make_result("Section A", 9.0),
        make_result("Section B", 7.0),
        make_result("Section A", 5.0),
    ]

    features = calculate_rank_features(
        results,
        ["Section A", "Section B"],
    )

    assert features["best_score"] == 9.0
    assert features["second_score"] == 7.0
    assert features["third_score"] == 5.0
    assert features["score_gap"] == 2.0
    assert features["average_top_3"] == 7.0
    assert features["average_top_5"] == 7.0
    assert features["matching_top_5_count"] == 3
    assert features["matched_expected_section_count"] == 2
    assert features["unique_section_count"] == 2
    assert features["dominant_section_count"] == 2
    assert features["first_relevant_rank"] == 1


def test_only_first_five_results_contribute_to_features():
    results = [
        make_result("Other", 10.0),
        make_result("Other", 9.0),
        make_result("Other", 8.0),
        make_result("Other", 7.0),
        make_result("Section A", 6.0),
        make_result("Section B", 100.0),
    ]

    features = calculate_rank_features(results, ["Section B"])

    assert features["best_score"] == 10.0
    assert features["average_top_5"] == 8.0
    assert features["matching_top_5_count"] == 0
    assert features["matched_expected_section_count"] == 0
    assert features["first_relevant_rank"] is None


def test_missing_section_titles_are_handled():
    results = [
        make_result(None, 4.0),
        make_result("", 2.0),
    ]

    features = calculate_rank_features(results, ["Section A"])

    assert features["best_score"] == 4.0
    assert features["unique_section_count"] == 0
    assert features["dominant_section_count"] == 0
    assert features["matching_top_5_count"] == 0
