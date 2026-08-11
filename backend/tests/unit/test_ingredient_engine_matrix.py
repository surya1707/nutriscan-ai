"""
Direct, service-level tests for IngredientEngine -- no HTTP layer, no
FastAPI dependency injection. These call app/services/ingredient_engine.py
directly, so they run fast and pin down business logic (especially the
health-score algorithm) that the API-level tests in tests/functional/ only
exercise incidentally.

Parametrized across every entry in app/data/ecodes.json (30 entries) and
every app/services/ingredient_engine.py harmful_keywords entry (11
entries), so this suite fails immediately if the data file or matching
logic regresses for any ONE entry, not just "most" entries -- which is
exactly what caught the case-sensitivity bug documented below.
"""
import json
from pathlib import Path

import pytest

from app.services.ingredient_engine import IngredientEngine
from app.schemas.scan import IngredientResult

ECODES_PATH = Path(__file__).resolve().parent.parent.parent / "app" / "data" / "ecodes.json"
ECODES = json.loads(ECODES_PATH.read_text())

HARMFUL_KEYWORDS = [
    "high fructose corn syrup", "hfcs", "palm oil", "hydrogenated vegetable oil",
    "partially hydrogenated oil", "maltodextrin", "monosodium glutamate", "msg",
    "sodium benzoate", "artificial flavor", "artificial color",
]

# [CONFIRMED BUG - found by this test matrix, fully root-caused by direct
# experimentation with rapidfuzz, not assumed] app/services/ingredient_engine.py's
# fuzzy-match step lowercases the QUERY string but never lowercases the
# CHOICES list, and rebuilds that choices list from the original-case data
# on every single call:
#
#   lower_name = name.lower().strip()                             # query: lowercased
#   full_names = [e["full_name"] for e in self.ecodes]             # choices: ORIGINAL case, every time
#   match = process.extractOne(lower_name, full_names, scorer=fuzz.WRatio)
#
# fuzz.WRatio is case-sensitive, and this means a lowercased query can
# NEVER score a perfect 100 against ANY entry -- it is always penalized by
# at least the case difference. Confirmed directly:
#   fuzz.WRatio('sunset yellow fcf', 'sunset yellow fcf')  == 100.0
#   fuzz.WRatio('sunset yellow fcf', 'Sunset Yellow FCF')  ==  70.6
#
# SCOPE (measured across all 30 entries, not assumed from the 4 obvious
# cases): running every ecodes.json full_name through the REAL
# analyze_ingredients() method:
#   - 23 of 30 score below 90 due to the case penalty alone (fragile --
#     one small wording tweak to ecodes.json and any of these could tip
#     into the same failure as the ones below)
#   - 5 of 30 are CONFIRMED to fail actual identification outright (either
#     scoring below the 80-point threshold, or losing to a different,
#     wrong entry): E110, E129, E133, E150a, E412
#   - Of those 5, 4 produce a user-visible WRONG STATUS (E412 happens to
#     fall through to the correct status by coincidence via the "safe"
#     default, masking that its identification is still broken):
#       * "Sunset Yellow FCF" (danger)  -> scores 70.6, below threshold -> falls through to "safe"
#       * "Allura Red AC" (danger)      -> scores 69.2, below threshold -> falls through to "safe"
#       * "Brilliant Blue FCF" (caution)-> scores 72.2, below threshold -> falls through to "safe"
#       * "Plain Caramel" (safe)        -> scores 84.6 vs itself, but 85.5 vs the WRONG
#         entry "Sulphite ammonia caramel" (caution) -- actively MISCLASSIFIED,
#         not just missed
#
# This is a food-safety app silently failing (for ~13-17% of its own known
# additive database, depending on how you count) to flag known-dangerous
# additives when a user enters them in their real, natural product-label
# case -- which is the only case any real user would ever actually type.
#
# REMEDIATION: lowercase full_names before fuzzy matching, e.g.
#   full_names_lower = [n.lower() for n in full_names]
#   match = process.extractOne(lower_name, full_names_lower, scorer=fuzz.WRatio)
#   ecode_match = next(e for e in self.ecodes if e["full_name"].lower() == match[0])
_KNOWN_CASE_SENSITIVITY_BUG_FULL_NAMES = {
    "Sunset Yellow FCF",   # user-visible: falls through to wrong status "safe"
    "Allura Red AC",       # user-visible: falls through to wrong status "safe"
    "Brilliant Blue FCF",  # user-visible: falls through to wrong status "safe"
    "Plain Caramel",       # user-visible: actively misclassified as a different, wrong additive
}
# Identification is ALSO confirmed broken for E412 "Guar Gum" (scores 75.0,
# below threshold), but it happens to fall through to the "safe" default
# status, which coincidentally equals its real status -- so it doesn't
# belong in the status-equality xfail set above, but IS covered by the
# stricter test_ecode_actually_identified_by_real_label_full_name below,
# which checks that the match mechanism itself worked, not just that the
# output happened to look right.
_KNOWN_CASE_SENSITIVITY_BUG_IDENTIFICATION_ONLY = _KNOWN_CASE_SENSITIVITY_BUG_FULL_NAMES | {"Guar Gum"}


@pytest.fixture(scope="module")
def engine():
    return IngredientEngine()


def _mk(name, status, reason="no concerns"):
    return IngredientResult(name=name, status=status, reason=reason)


# ---------------------------------------------------------------------------
# E-code data integrity matrix (60 cases: 30 by code name, 30 by full name)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ecode", ECODES, ids=[e["name"] for e in ECODES])
def test_ecode_matched_by_code_name(engine, ecode):
    """
    CATEGORY: Business Logic / Data Integrity
    TITLE: Every E-code in ecodes.json is correctly classified by its own code name
    OBJECTIVE: Exercises the direct substring-match step (step 1 in
      analyze_ingredients). A failure here for a single entry means either
      ecodes.json or the matching logic broke for that specific additive.
    SEVERITY: High
    """
    result = engine.analyze_ingredients([ecode["name"]])[0]
    assert result.status == ecode["status"]
    assert ecode["full_name"] in result.reason
    assert ecode["reason"] in result.reason


@pytest.mark.parametrize("ecode", ECODES, ids=[e["name"] for e in ECODES])
def test_ecode_matched_by_real_label_full_name(engine, ecode):
    """
    CATEGORY: Business Logic / Data Integrity
    TITLE: [FINDING - see module docstring] Every E-code should be correctly
      classified when entered in its real, natural product-label case
    OBJECTIVE: Exercises the fuzzy-match step (step 2) using the exact
      capitalization a user would see on a real ingredient label -- not a
      pre-lowercased convenience string. 4 of 30 entries are confirmed
      broken by a case-sensitivity bug in the fuzzy matcher; see the module
      docstring for the full root-cause analysis with exact WRatio scores.
    SEVERITY: High
    """
    if ecode["full_name"] in _KNOWN_CASE_SENSITIVITY_BUG_FULL_NAMES:
        pytest.xfail(
            f"[CONFIRMED BUG] {ecode['full_name']!r} is misclassified due to "
            "case-sensitive fuzzy matching -- see module docstring for the "
            "exact confirmed WRatio scores and remediation."
        )
    result = engine.analyze_ingredients([ecode["full_name"]])[0]
    assert result.status == ecode["status"], (
        f"{ecode['full_name']!r} classified as {result.status!r}, expected "
        f"{ecode['status']!r} -- if this is a NEW case-sensitivity casualty, "
        "add it to _KNOWN_CASE_SENSITIVITY_BUG_FULL_NAMES until the "
        "underlying case-sensitivity bug is fixed."
    )


@pytest.mark.parametrize("ecode", ECODES, ids=[e["name"] for e in ECODES])
def test_ecode_actually_identified_by_real_label_full_name(engine, ecode):
    """
    CATEGORY: Business Logic / Data Integrity
    TITLE: [FINDING - see module docstring] The matcher should identify the
      CORRECT specific E-code entry, not just happen to land on the right
      status by coincidence
    OBJECTIVE: Stricter than test_ecode_matched_by_real_label_full_name --
      checks that the E-code's own full_name appears in the result reason
      (proof the right entry was actually selected), not just that the
      final status string happens to match. This catches one additional
      casualty (E412 "Guar Gum") that test_ecode_matched_by_real_label_full_name
      misses, because Guar Gum's broken match happens to fall through to a
      "safe" default that coincidentally equals its real status -- the
      identification is still broken, it's just invisible if you only check
      the final status.
    SEVERITY: Medium
    """
    if ecode["full_name"] in _KNOWN_CASE_SENSITIVITY_BUG_IDENTIFICATION_ONLY:
        pytest.xfail(
            f"[CONFIRMED BUG] {ecode['full_name']!r} is not actually identified "
            "by the fuzzy matcher due to the case-sensitivity bug -- see module "
            "docstring. May coincidentally produce the right status via the "
            "'safe' default without this test catching it if you only check status."
        )
    result = engine.analyze_ingredients([ecode["full_name"]])[0]
    assert ecode["full_name"] in result.reason, (
        f"{ecode['full_name']!r} was not correctly identified (reason: {result.reason!r}) "
        "-- if this is a NEW casualty of the case-sensitivity bug, add it to "
        "_KNOWN_CASE_SENSITIVITY_BUG_IDENTIFICATION_ONLY."
    )


# ---------------------------------------------------------------------------
# Harmful keyword matrix (11 cases)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keyword", HARMFUL_KEYWORDS)
def test_harmful_keyword_flagged_as_caution(engine, keyword):
    """
    CATEGORY: Business Logic / Data Integrity
    TITLE: Every non-E-code harmful keyword is flagged as caution
    SEVERITY: Medium
    """
    result = engine.analyze_ingredients([keyword])[0]
    assert result.status == "caution"


@pytest.mark.parametrize("keyword", HARMFUL_KEYWORDS)
def test_harmful_keyword_flagged_within_a_longer_ingredient_string(engine, keyword):
    """
    CATEGORY: Business Logic
    TITLE: A harmful keyword embedded inside a longer ingredient description is still caught
    OBJECTIVE: Real ingredient labels rarely list bare keywords -- confirms
      substring matching works within realistic label text, e.g.
      "contains high fructose corn syrup (2%)".
    SEVERITY: Medium
    """
    result = engine.analyze_ingredients([f"contains {keyword} (2%)"])[0]
    assert result.status == "caution"


def test_ecodes_json_has_no_duplicate_codes(engine):
    """
    CATEGORY: Data Integrity
    TITLE: ecodes.json has no duplicate "name" entries
    OBJECTIVE: A duplicate would mean whichever entry appears first in the
      list silently shadows the other for the direct-match step -- the
      second entry would be permanently unreachable dead data.
    SEVERITY: Medium
    """
    names = [e["name"] for e in ECODES]
    assert len(names) == len(set(names)), f"duplicates found: {[n for n in names if names.count(n) > 1]}"


def test_ecodes_json_every_entry_has_required_fields(engine):
    """
    CATEGORY: Data Integrity
    TITLE: Every ecodes.json entry has all required fields with valid values
    SEVERITY: Medium
    """
    for entry in ECODES:
        assert entry["name"].upper().startswith("E")
        assert entry["status"] in ("safe", "caution", "danger")
        assert len(entry["full_name"]) > 0
        assert len(entry["reason"]) > 0


# ---------------------------------------------------------------------------
# Allergy profile matching (direct)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("allergy,ingredient", [
    ("peanut", "peanut butter"),
    ("peanut", "contains peanuts"),
    ("dairy", "dairy solids"),
    ("gluten", "wheat gluten"),
    ("shellfish", "shellfish extract"),
    ("soy", "soy lecithin"),
    ("egg", "egg white powder"),
])
def test_allergy_profile_flags_matching_ingredient_as_danger(engine, allergy, ingredient):
    """
    CATEGORY: Business Logic
    TITLE: A saved allergy correctly flags a matching ingredient as danger,
      overriding whatever its E-code/keyword status would otherwise be
    SEVERITY: Critical
    """
    result = engine.analyze_ingredients([ingredient], user_profile={"allergies": [allergy]})[0]
    assert result.status == "danger"
    assert f"Matches your allergy: {allergy}" in result.reason


def test_allergy_check_is_case_insensitive(engine):
    """
    CATEGORY: Business Logic
    TITLE: Allergy matching works regardless of the case used for either the
      saved allergy or the ingredient name
    SEVERITY: High
    """
    result = engine.analyze_ingredients(["PEANUT BUTTER"], user_profile={"allergies": ["Peanut"]})[0]
    assert result.status == "danger"


def test_allergy_takes_priority_over_ecode_status(engine):
    """
    CATEGORY: Business Logic
    TITLE: A profile allergy match overrides an otherwise "safe" E-code classification
    OBJECTIVE: analyze_ingredients checks is_allergen BEFORE ecode_match in
      its final if/elif chain -- confirms that ordering holds even when the
      ingredient would otherwise resolve as a "safe" E-code.
    SEVERITY: Critical
    """
    # E202 (Potassium Sorbate) is "safe" in ecodes.json -- but if someone
    # is (implausibly, for the sake of proving precedence) allergic to it,
    # the ingredient text itself must contain the allergy substring for the
    # allergy check (`allergy.lower() in lower_name`) to fire at all.
    result = engine.analyze_ingredients(
        ["Potassium Sorbate"], user_profile={"allergies": ["Potassium Sorbate"]}
    )[0]
    assert result.status == "danger"


def test_empty_allergy_list_does_not_flag_anything(engine):
    """
    CATEGORY: Business Logic
    TITLE: An empty allergies list behaves identically to no profile at all
    SEVERITY: Medium
    """
    result = engine.analyze_ingredients(["peanut butter"], user_profile={"allergies": []})[0]
    assert result.status != "danger"


# ---------------------------------------------------------------------------
# calculate_hs_score: NOVA deduction (boundary-verified)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nova_class,expected_deduction,expected_final", [
    (1, 0.0, 100),
    (2, 6.7, 93),
    (3, 13.3, 87),
    (4, 20.0, 80),
])
def test_nova_deduction_formula_at_every_class(engine, nova_class, expected_deduction, expected_final):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: NOVA deduction follows (nova_class - 1) * 6.67, capped at 20, for every class 1-4
    OBJECTIVE: This scoring formula has no dedicated boundary test in the
      original suite (only nova_class=1 and nova_class=4 were touched, and
      only combined with other deductions). Verified exact values by direct
      experimentation before writing these assertions.
    SEVERITY: High
    """
    result = engine.calculate_hs_score([_mk("water", "safe")], nova_class=nova_class)
    assert result["breakdown"]["novaDeduction"] == expected_deduction
    assert result["final_score"] == expected_final


# ---------------------------------------------------------------------------
# calculate_hs_score: additive deduction position-weighting (verified)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("position,expected_deduction", [
    (0, 15.0),  # multiplier x3
    (1, 10.0),  # multiplier x2
    (2, 10.0),  # multiplier x2
    (3, 5.0),   # multiplier x1
    (4, 5.0),
    (5, 5.0),
    (6, 2.5),   # multiplier x0.5
    (7, 2.5),
])
def test_additive_deduction_position_weighting(engine, position, expected_deduction):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: A flagged ingredient's position in the list changes its score penalty weight
    OBJECTIVE: FSSAI-style labels list ingredients by descending weight, so
      the algorithm weights earlier positions more heavily (x3 for position
      0, x2 for positions 1-2, x1 for positions 3-5, x0.5 for position 6+).
      Verified exact expected values by direct experimentation with the
      real calculate_hs_score before writing these assertions -- not
      derived purely by reading the source.
    SEVERITY: High
    """
    filler = [_mk(f"filler{i}", "safe") for i in range(position)]
    ingredients = filler + [_mk("flagged", "caution")]
    result = engine.calculate_hs_score(ingredients, nova_class=1)
    assert result["breakdown"]["additiveDeduction"] == expected_deduction


def test_additive_deduction_caps_at_30(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: additiveDeduction never exceeds 30, even when uncapped math would produce more
    OBJECTIVE: Two "danger" (non-allergy) ingredients at positions 0 and 1
      would sum to 10*3 + 10*2 = 50 uncapped; confirms the min(30.0, ...) cap.
    SEVERITY: Medium
    """
    ingredients = [_mk("bad1", "danger", "synthetic dye"), _mk("bad2", "danger", "synthetic dye")]
    result = engine.calculate_hs_score(ingredients, nova_class=1)
    assert result["breakdown"]["additiveDeduction"] == 30.0


def test_additive_deduction_sugar_keyword_bonus(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: A "sugar"/"syrup"/"palm oil"/"fructose" name adds +4 to the base penalty
    OBJECTIVE: "caution" base penalty (5) + sugar bonus (4) = 9, x3 position
      multiplier at position 0 = 27. Verified exact value directly.
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score([_mk("cane sugar", "caution")], nova_class=1)
    assert result["breakdown"]["additiveDeduction"] == 27.0


def test_allergy_matched_ingredients_excluded_from_additive_deduction(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: An allergy-matched "danger" ingredient contributes to allergenDeduction, not additiveDeduction
    OBJECTIVE: Confirms no double-counting -- the additive-penalty branch
      explicitly excludes items whose reason mentions "allergy".
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score(
        [_mk("peanut", "danger", "Matches your allergy: peanut")], nova_class=1
    )
    assert result["breakdown"]["additiveDeduction"] == 0.0
    assert result["breakdown"]["allergenDeduction"] == 40


# ---------------------------------------------------------------------------
# calculate_hs_score: allergen deduction (verified)
# ---------------------------------------------------------------------------

def test_allergen_deduction_single_hit(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: A single allergy hit deducts exactly 40 points
    SEVERITY: High
    """
    result = engine.calculate_hs_score(
        [_mk("peanut", "danger", "Matches your allergy: peanut")], nova_class=1
    )
    assert result["breakdown"]["allergenDeduction"] == 40


def test_allergen_deduction_caps_at_40_for_multiple_hits(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: Two allergy hits still deduct only 40 (capped), not 80
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score(
        [
            _mk("peanut", "danger", "Matches your allergy: peanut"),
            _mk("milk", "danger", "Matches your allergy: milk"),
        ],
        nova_class=1,
    )
    assert result["breakdown"]["allergenDeduction"] == 40


def test_allergen_deduction_zero_with_no_hits(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: allergenDeduction is 0 when nothing matches a profile allergy
    SEVERITY: Low
    """
    result = engine.calculate_hs_score([_mk("water", "safe")], nova_class=1)
    assert result["breakdown"]["allergenDeduction"] == 0


# ---------------------------------------------------------------------------
# calculate_hs_score: condition deduction (verified)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("condition,ingredient_name,expected_deduction", [
    ("Diabetes", "sugar", 15),
    ("Diabetes", "corn syrup", 15),
    ("Diabetes", "maltodextrin", 15),
    ("Hypertension", "sodium chloride", 12),
    ("Hypertension", "table salt", 12),
    ("High Cholesterol", "palm oil", 10),
    ("High Cholesterol", "saturated fat blend", 10),
    ("High Cholesterol", "beef lard", 10),
])
def test_condition_deduction_per_condition(engine, condition, ingredient_name, expected_deduction):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: Each medical condition correctly deducts points when a matching keyword is present
    OBJECTIVE: Verified each (condition, keyword) pair's exact deduction
      value directly against calculate_hs_score before writing assertions.
    SEVERITY: High
    """
    result = engine.calculate_hs_score(
        [_mk(ingredient_name, "caution")], nova_class=1, user_profile={"conditions": [condition]}
    )
    assert result["breakdown"]["conditionDeduction"] == expected_deduction


def test_condition_deduction_no_match_is_zero(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: A condition with no matching keyword in the ingredient list deducts 0
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score(
        [_mk("water", "safe")], nova_class=1, user_profile={"conditions": ["Diabetes"]}
    )
    assert result["breakdown"]["conditionDeduction"] == 0


def test_condition_deduction_all_three_caps_at_20(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: All three conditions matching simultaneously caps at 20, not 15+12+10=37
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score(
        [_mk("sugar sodium palm oil blend", "caution")],
        nova_class=1,
        user_profile={"conditions": ["Diabetes", "Hypertension", "High Cholesterol"]},
    )
    assert result["breakdown"]["conditionDeduction"] == 20


def test_unrecognized_condition_name_is_silently_ignored(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: [FINDING] A condition name not in the hardcoded set (Diabetes/
      Hypertension/High Cholesterol) is silently ignored, deducting nothing
    OBJECTIVE: schemas/user.py's "conditions" field is a free-text
      List[str] with no validation against a fixed enum -- a user (or a
      future frontend update) could save "Celiac Disease" or "Kidney
      Disease" and it would simply never affect scoring, with no error or
      warning anywhere.
    IMPACT: Low-to-Medium. Not a security issue, but a silent correctness
      gap: the scoring algorithm's condition-awareness only covers 3
      hardcoded conditions no matter what the user actually saves.
    REMEDIATION: either constrain "conditions" to a known enum at the
      schema level, or make calculate_hs_score's condition matching
      data-driven instead of three hardcoded if-blocks.
    SEVERITY: Low
    """
    result = engine.calculate_hs_score(
        [_mk("gluten wheat flour", "caution")],
        nova_class=1,
        user_profile={"conditions": ["Celiac Disease"]},
    )
    assert result["breakdown"]["conditionDeduction"] == 0


# ---------------------------------------------------------------------------
# calculate_hs_score: end-to-end floor and combined scenarios
# ---------------------------------------------------------------------------

def test_final_score_floors_at_zero_not_negative(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: A worst-case combination (allergens + NOVA 4 + capped additives +
      all conditions) floors the score at exactly 0, never negative
    OBJECTIVE: 40 (allergen) + 20 (nova) + 30 (additive, capped) + 20
      (condition) = 110 raw deduction against a 100-point scale. Confirmed
      directly this produces final_score == 0, not -10.
    SEVERITY: High
    """
    ingredients = [
        _mk("peanut", "danger", "Matches your allergy: peanut"),
        _mk("sugar dye", "danger", "synthetic, contains sugar"),
        _mk("sodium palm oil additive", "danger", "synthetic, sodium palm oil"),
    ]
    result = engine.calculate_hs_score(
        ingredients,
        nova_class=4,
        user_profile={"conditions": ["Diabetes", "Hypertension", "High Cholesterol"]},
    )
    assert result["final_score"] == 0
    assert result["breakdown"] == {
        "allergenDeduction": 40,
        "novaDeduction": 20,
        "additiveDeduction": 30.0,
        "conditionDeduction": 20,
    }


def test_all_safe_ingredients_score_100(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: An all-safe ingredient list with NOVA class 1 scores a perfect 100
    OBJECTIVE: Deliberately avoids "sugar"/"syrup"/"palm oil"/"fructose" in
      any ingredient name here -- see
      test_safe_status_ingredient_still_penalized_if_name_contains_sugar_keyword
      below for why those specific words are not a safe choice for this test.
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score(
        [_mk("water", "safe"), _mk("salt", "safe"), _mk("starch", "safe")], nova_class=1
    )
    assert result["final_score"] == 100


def test_safe_status_ingredient_still_penalized_if_name_contains_sugar_keyword(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: [FINDING] An ingredient classified "safe" by analyze_ingredients
      can still be scored down by calculate_hs_score if its name contains
      "sugar", "syrup", "palm oil", or "fructose"
    OBJECTIVE: calculate_hs_score's additive-penalty loop has a SEPARATE,
      independent keyword check -- `if any(x in name_lower for x in
      ["sugar", "syrup", "palm oil", "fructose"])` -- that applies
      regardless of the ingredient's status field. A plain ingredient named
      "sugar" is classified "safe" by analyze_ingredients (it's not in
      ecodes.json or harmful_keywords), but calculate_hs_score still
      deducts points for it via this separate name-based check. Confirmed
      directly: ["water","salt","sugar"] at nova_class=1 scores 92, not 100,
      solely because of "sugar" appearing third in the list.
    IMPACT: Not a security issue, and arguably reasonable product behavior
      (added sugar probably SHOULD cost points even if it's not flagged as
      an "unsafe" ingredient) -- but it's undocumented, inconsistent with
      the ingredient's own reported status ("No major concerns found." next
      to a score deduction is confusing for a user), and worth being a
      deliberate, documented design choice rather than an incidental side
      effect discovered by testing.
    SEVERITY: Low
    """
    result = engine.calculate_hs_score(
        [_mk("water", "safe"), _mk("salt", "safe"), _mk("sugar", "safe")], nova_class=1
    )
    assert result["final_score"] == 92
    assert result["breakdown"]["additiveDeduction"] == 8.0


def test_empty_ingredient_list_scores_100(engine):
    """
    CATEGORY: Business Logic / Scoring Algorithm
    TITLE: An empty ingredient list (e.g. a barcode product with no listed
      ingredients) still produces a valid, non-crashing score
    SEVERITY: Medium
    """
    result = engine.calculate_hs_score([], nova_class=1)
    assert result["final_score"] == 100
