from app.services.ingredient_engine import IngredientEngine
from app.schemas.scan import IngredientResult

def test_ingredient_engine_analyze():
    engine = IngredientEngine()
    
    # All-clear case
    safe_ingredients = ["water", "salt", "sugar"]
    results = engine.analyze_ingredients(safe_ingredients)
    
    assert len(results) == 3
    assert results[0].status == "safe"
    
    # Flagged ingredient case
    flagged_ingredients = ["E621", "palm oil", "monosodium glutamate"]
    results = engine.analyze_ingredients(flagged_ingredients)
    
    assert len(results) == 3
    assert results[0].status in ["caution", "danger"]  # MSG/E621 depends on ecodes.json, but likely caution
    assert results[1].status == "caution" # palm oil
    assert results[2].status == "caution" # monosodium glutamate
    
    # Profile-based allergy case
    profile = {"allergies": ["peanut"]}
    allergy_ingredients = ["peanut butter", "salt"]
    results = engine.analyze_ingredients(allergy_ingredients, user_profile=profile)
    assert results[0].status == "danger"
    assert "Matches your allergy: peanut" in results[0].reason
    assert results[1].status == "safe"

def test_ingredient_engine_score():
    engine = IngredientEngine()
    
    # All safe
    safe_results = [
        IngredientResult(name="water", status="safe", reason="No major concerns found.")
    ]
    score_data = engine.calculate_hs_score(safe_results, nova_class=1)
    assert score_data["final_score"] == 100
    assert score_data["breakdown"]["allergenDeduction"] == 0
    assert score_data["breakdown"]["novaDeduction"] == 0
    
    # High risk (allergy)
    danger_results = [
        IngredientResult(name="peanut", status="danger", reason="Matches your allergy: peanut")
    ]
    score_data = engine.calculate_hs_score(danger_results, nova_class=4)
    # nova deduction: (4-1)*6.67 = 20
    # allergen deduction: 40
    # additive deduction: 0 (allergy deduction applies instead of standard danger)
    assert score_data["final_score"] == 40
    assert score_data["breakdown"]["allergenDeduction"] == 40
    assert score_data["breakdown"]["novaDeduction"] == 20
