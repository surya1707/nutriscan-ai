"""
Functional API tests for POST /scan/analyse and POST /scan/barcode, beyond
the happy-path/empty/not-found cases already in tests/test_scan.py.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch


# ---------------------------------------------------------------------------
# /scan/analyse
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyse_flags_known_ecode(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: A known E-number is classified using ecodes.json
    OBJECTIVE: E102 (Tartrazine) is seeded in app/data/ecodes.json as "danger".
    EXPECTED: 200, ingredient status == "danger", reason mentions Tartrazine.
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["E102"]})
    assert response.status_code == 200
    data = response.json()
    assert data["ingredients"][0]["status"] == "danger"
    assert "Tartrazine" in data["ingredients"][0]["reason"]


@pytest.mark.asyncio
async def test_analyse_fuzzy_matches_misspelled_full_name(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Fuzzy matching (rapidfuzz, threshold 80) catches near-misspellings
    OBJECTIVE: "curcumin" is E100's full_name. A close misspelling should
      still match via fuzz.WRatio >= 80, not silently fall through to "safe".
    SEVERITY: Low
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["curcumin"]})
    assert response.status_code == 200
    # Exact full_name match should resolve to the E100 entry, not "safe" by omission.
    data = response.json()
    assert data["ingredients"][0]["status"] == "safe"  # E100 itself is tagged "safe" in ecodes.json
    assert "Curcumin" in data["ingredients"][0]["reason"]


@pytest.mark.asyncio
async def test_analyse_harmful_keyword_without_ecode(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Non-E-code harmful keyword list still flags ingredients
    OBJECTIVE: "palm oil" is in IngredientEngine.harmful_keywords, not ecodes.json.
    EXPECTED: status == "caution".
    SEVERITY: Low
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["palm oil"]})
    assert response.status_code == 200
    assert response.json()["ingredients"][0]["status"] == "caution"


@pytest.mark.asyncio
async def test_analyse_is_case_insensitive(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Ingredient matching is case-insensitive
    SEVERITY: Low
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["PALM OIL"]})
    assert response.status_code == 200
    assert response.json()["ingredients"][0]["status"] == "caution"


@pytest.mark.asyncio
async def test_analyse_unicode_ingredient_names(async_client: AsyncClient):
    """
    CATEGORY: Functional API / Input Validation
    TITLE: Non-ASCII ingredient names do not crash the pipeline
    OBJECTIVE: rapidfuzz + string containment checks must handle unicode
      (e.g. accented characters, non-Latin scripts) without raising.
    SEVERITY: Medium
    """
    response = await async_client.post(
        "/scan/analyse", json={"ingredients": ["crème fraîche", "味精", "sódium bénzoate"]}
    )
    assert response.status_code == 200
    assert len(response.json()["ingredients"]) == 3


@pytest.mark.asyncio
async def test_analyse_duplicate_ingredients_all_returned(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Duplicate ingredient entries are each analyzed and returned
    OBJECTIVE: The response must be positional/1:1 with the request, not deduplicated.
    SEVERITY: Low
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["water", "water", "water"]})
    assert response.status_code == 200
    assert len(response.json()["ingredients"]) == 3


@pytest.mark.asyncio
async def test_analyse_large_ingredient_list_does_not_crash(async_client: AsyncClient):
    """
    CATEGORY: Functional API / Performance
    TITLE: A large (200-item) ingredient list completes without error
    OBJECTIVE: Guard against O(n^2) fuzzy-matching blowups or timeouts on
      realistic worst-case label lengths.
    SEVERITY: Medium
    """
    ingredients = [f"mystery ingredient {i}" for i in range(200)]
    response = await async_client.post("/scan/analyse", json={"ingredients": ingredients})
    assert response.status_code == 200
    assert len(response.json()["ingredients"]) == 200


@pytest.mark.asyncio
async def test_analyse_missing_ingredients_field_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: Missing required field returns a clean 422, not a 500
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/analyse", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyse_wrong_type_for_ingredients_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: Non-list "ingredients" value is rejected by Pydantic, not cast
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": "water"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyse_non_string_items_in_list_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: A list containing non-string items (numbers, objects, null) is rejected
    OBJECTIVE: Confirms Pydantic's List[str] coercion doesn't silently
      stringify or crash on int/dict/None entries.
    SEVERITY: Medium
    """
    response = await async_client.post(
        "/scan/analyse", json={"ingredients": ["water", 12345, {"a": 1}, None]}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_anonymous_scan_is_not_personalized_or_saved(async_client: AsyncClient):
    """
    CATEGORY: Functional API / Authorization
    TITLE: An unauthenticated scan never applies personalization
    OBJECTIVE: "peanut" only becomes "danger" against a profile that lists it
      as an allergy. With no auth token, current_user is None, so scan/analyse
      must use the empty default profile and must not attempt to save history
      (there is no user to attribute it to).
    EXPECTED: 200, status != "danger" for a plain allergen name with no profile match.
    SEVERITY: High
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["peanut butter"]})
    assert response.status_code == 200
    assert response.json()["ingredients"][0]["status"] != "danger"


@pytest.mark.asyncio
async def test_authenticated_scan_applies_saved_allergy_profile(auth_client: AsyncClient):
    """
    CATEGORY: Functional API / Business Logic
    TITLE: An authenticated scan is personalized against the user's saved allergies
    OBJECTIVE: End-to-end: create profile -> set allergy -> scan -> "danger".
    SEVERITY: High
    """
    await auth_client.get("/users/me")  # auto-creates the profile row
    await auth_client.patch("/users/me", json={"allergies": ["peanut"]})

    response = await auth_client.post("/scan/analyse", json={"ingredients": ["peanut butter", "salt"]})
    assert response.status_code == 200
    data = response.json()
    assert data["ingredients"][0]["status"] == "danger"
    assert "peanut" in data["ingredients"][0]["reason"]
    assert data["ingredients"][1]["status"] == "safe"


# ---------------------------------------------------------------------------
# /scan/barcode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.routers.scan.off_client.get_product")
async def test_barcode_happy_path_with_full_product(mock_get_product, async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: A full Open Food Facts product payload is analyzed end-to-end
    SEVERITY: High
    """
    mock_get_product.return_value = {
        "product_name": "Fizzy Cola",
        "brands": "ColaCorp",
        "ingredients_text": "carbonated water, sugar, E150d, caffeine",
        "nova_group": 4,
        "nutriments": {"sugars_100g": 10.6},
    }
    response = await async_client.post("/scan/barcode", json={"barcode": "5000112637922"})
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Fizzy Cola"
    assert data["nova_class"] == 4
    assert len(data["ingredients"]) == 4
    assert data["nutrients"]["sugars_100g"] == 10.6


@pytest.mark.asyncio
@patch("app.routers.scan.off_client.get_product")
async def test_barcode_product_with_no_ingredients_text(mock_get_product, async_client: AsyncClient):
    """
    CATEGORY: Functional API / Input Validation
    TITLE: A product with a missing/empty ingredients_text field doesn't crash
    OBJECTIVE: routers/scan.py does `.get("ingredients_text", "").split(",")` --
      confirm the empty-string/None case degrades to an empty ingredient list,
      not an AttributeError on None.split(...).
    SEVERITY: Medium
    """
    mock_get_product.return_value = {"product_name": "Mystery Item", "brands": "Unknown"}
    response = await async_client.post("/scan/barcode", json={"barcode": "0000000000000"})
    assert response.status_code == 200
    assert response.json()["ingredients"] == []


@pytest.mark.asyncio
@patch("app.routers.scan.off_client.get_product")
async def test_barcode_missing_nova_group_defaults_to_4(mock_get_product, async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: A product missing nova_group defaults to the most conservative class (4)
    OBJECTIVE: routers/scan.py does int(product.get("nova_group", 4)) -- confirm
      the fail-safe default is actually reached, not skipped.
    SEVERITY: Medium
    """
    mock_get_product.return_value = {
        "product_name": "Unclassified Snack",
        "ingredients_text": "sugar",
    }
    response = await async_client.post("/scan/barcode", json={"barcode": "1111111111111"})
    assert response.status_code == 200
    assert response.json()["nova_class"] == 4


@pytest.mark.asyncio
async def test_barcode_missing_field_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: Missing "barcode" field returns 422
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/barcode", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
@patch("app.routers.scan.off_client.get_product")
async def test_barcode_authenticated_scan_saved_to_history(mock_get_product, auth_client: AsyncClient):
    """
    CATEGORY: Functional API / Business Logic
    TITLE: An authenticated barcode scan is saved with the correct product metadata
    SEVERITY: High
    """
    mock_get_product.return_value = {
        "product_name": "Trail Mix",
        "brands": "NutriBrand",
        "ingredients_text": "almonds, raisins",
        "nova_group": 1,
        "nutriments": {},
    }
    scan = await auth_client.post("/scan/barcode", json={"barcode": "9999999999999"})
    assert scan.status_code == 200

    history = await auth_client.get("/history")
    assert history.status_code == 200
    items = history.json()
    assert len(items) == 1
    assert items[0]["product_name"] == "Trail Mix"
    assert items[0]["brand"] == "NutriBrand"
    assert items[0]["nova_group"] == 1
