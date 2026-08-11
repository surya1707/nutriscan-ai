"""
Direct, service-level tests for NovaClassifier -- no HTTP layer.

Parametrized across all 20 entries in NovaClassifier.ultra_processed_markers
so a regression in any single marker string is caught immediately, plus
every documented boundary in the classify() rule chain. Every expected
value below was verified directly against the real classify() method
before being written as an assertion.
"""
import pytest

from app.services.nova_classifier import NovaClassifier

MARKERS = [
    "syrup", "artificial flavor", "colour", "color", "modified starch",
    "emulsifier", "preservative", "sweetener", "hydrolysed", "interesterified",
    "hydrogenated", "maltodextrin", "dextrose", "inverted sugar",
    "potassium sorbate", "sodium benzoate", "aspartame", "sucralose",
    "monosodium glutamate", "carrageenan",
]


@pytest.fixture(scope="module")
def classifier():
    return NovaClassifier()


@pytest.mark.parametrize("marker", MARKERS)
def test_each_ultra_processed_marker_individually_triggers_class_3(classifier, marker):
    """
    CATEGORY: Business Logic / Data Integrity
    TITLE: Every ultra_processed_markers entry, alone, triggers at least class 3
    OBJECTIVE: A regression in this list (typo, removed entry) would
      silently under-classify processed foods. Confirms each of the 20
      markers, in isolation (marker_count == 1, well under the 15-item
      length threshold), correctly triggers the "marker_count >= 1" rule.
    SEVERITY: High
    """
    result = classifier.classify(["apple", marker])
    assert result == 3


def test_marker_matching_is_case_insensitive(classifier):
    """
    CATEGORY: Business Logic
    TITLE: Marker matching works regardless of the ingredient's capitalization
    SEVERITY: Medium
    """
    assert classifier.classify(["apple", "SYRUP"]) == 3
    assert classifier.classify(["apple", "SoDiUm BeNzOaTe"]) == 3


def test_marker_matched_within_a_longer_ingredient_string(classifier):
    """
    CATEGORY: Business Logic
    TITLE: A marker embedded inside a longer, realistic ingredient description is still caught
    SEVERITY: Medium
    """
    # "sodium benzoate" and "preservative" are both markers, but they appear
    # inside ONE ingredient string here -- marker_count counts distinct
    # markers found in the joined text, giving 2 (not double-counted per
    # ingredient), which lands on class 3 (the "3+ markers" rule needs 3).
    assert classifier.classify(["apple", "contains sodium benzoate as a preservative"]) == 3


@pytest.mark.parametrize("marker_count,expected_class", [(2, 3), (3, 4)])
def test_three_marker_threshold_boundary(classifier, marker_count, expected_class):
    """
    CATEGORY: Business Logic
    TITLE: Exactly 3 distinct markers triggers class 4; 2 markers stays at class 3
    OBJECTIVE: Verified the exact boundary directly: 2 markers -> 3, 3 markers -> 4.
    SEVERITY: High
    """
    candidate_markers = ["syrup", "preservative", "sweetener"][:marker_count]
    result = classifier.classify(["apple"] + candidate_markers)
    assert result == expected_class


@pytest.mark.parametrize("length,expected_class", [(15, 3), (16, 4)])
def test_fifteen_item_length_threshold_boundary(classifier, length, expected_class):
    """
    CATEGORY: Business Logic
    TITLE: An ingredient list of exactly 15 items stays under the ultra-processed
      length threshold; 16 items crosses it (regardless of marker count)
    OBJECTIVE: `marker_count >= 3 or len(ingredients) > 15` -- verified the
      exact off-by-one boundary directly (15 items -> False, still class 3
      via the length>8 rule; 16 items -> True, class 4).
    SEVERITY: High
    """
    result = classifier.classify([f"ingredient_{i}" for i in range(length)])
    assert result == expected_class


@pytest.mark.parametrize("length,expected_class", [(8, 2), (9, 3)])
def test_eight_item_length_threshold_boundary(classifier, length, expected_class):
    """
    CATEGORY: Business Logic
    TITLE: An ingredient list of exactly 8 items (0 markers) stays at class 2; 9 items crosses to class 3
    OBJECTIVE: `marker_count >= 1 or len(ingredients) > 8` -- verified the
      exact boundary directly with 0 markers present.
    SEVERITY: Medium
    """
    result = classifier.classify([f"ingredient_{i}" for i in range(length)])
    assert result == expected_class


@pytest.mark.parametrize("length,expected_class", [(3, 1), (4, 2)])
def test_three_item_length_threshold_boundary(classifier, length, expected_class):
    """
    CATEGORY: Business Logic
    TITLE: An ingredient list of exactly 3 items (no markers, no oil/sugar) stays
      at class 1 (unprocessed); 4 items crosses to class 2
    OBJECTIVE: `len(ingredients) > 3 or "oil" in all_text or "sugar" in
      all_text` -- verified the exact boundary directly.
    SEVERITY: Medium
    """
    result = classifier.classify([f"ingredient_{i}" for i in range(length)])
    assert result == expected_class


@pytest.mark.parametrize("keyword", ["oil", "sugar"])
def test_oil_or_sugar_keyword_triggers_class_2_even_with_one_ingredient(classifier, keyword):
    """
    CATEGORY: Business Logic
    TITLE: "oil" or "sugar" anywhere in the ingredient text triggers at
      least class 2, even for a single-item list well under every length threshold
    SEVERITY: Medium
    """
    result = classifier.classify([f"organic cane {keyword}" if keyword == "sugar" else f"virgin olive {keyword}"])
    assert result == 2


def test_single_plain_ingredient_is_class_1(classifier):
    """
    CATEGORY: Business Logic
    TITLE: A single plain, unprocessed-sounding ingredient with no markers/oil/sugar is class 1
    SEVERITY: Medium
    """
    assert classifier.classify(["apple"]) == 1


def test_empty_ingredient_list_does_not_crash(classifier):
    """
    CATEGORY: Business Logic / Input Validation
    TITLE: An empty ingredient list classifies as 1 (unprocessed) rather than crashing
    OBJECTIVE: Relevant for a barcode product with no listed ingredients text.
    SEVERITY: Medium
    """
    assert classifier.classify([]) == 1


def test_all_20_markers_present_together_is_class_4(classifier):
    """
    CATEGORY: Business Logic
    TITLE: An ingredient list containing every known marker classifies as class 4
    SEVERITY: Low
    """
    result = classifier.classify(["apple"] + MARKERS)
    assert result == 4
