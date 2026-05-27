import json
import os
from typing import List, Dict, Optional
from rapidfuzz import process, fuzz
from ..schemas.scan import IngredientResult, ScoreBreakdown

class IngredientEngine:
    def __init__(self):
        # Load E-codes
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "ecodes.json")
        with open(data_path, "r") as f:
            self.ecodes = json.load(f)
        
        # Load common harmful ingredients (non-E-code)
        self.harmful_keywords = {
            "high fructose corn syrup": "High fructose content linked to metabolic issues.",
            "hfcs": "High fructose corn syrup.",
            "palm oil": "High in saturated fats; environmental concerns.",
            "hydrogenated vegetable oil": "Contains trans fats.",
            "partially hydrogenated oil": "Source of trans fats.",
            "maltodextrin": "High glycemic index; triggers blood sugar spikes.",
            "monosodium glutamate": "Flavor enhancer; sensitivity concerns.",
            "msg": "Flavor enhancer; sensitivity concerns.",
            "sodium benzoate": "Artificial preservative.",
            "artificial flavor": "Synthetic chemical flavoring.",
            "artificial color": "Synthetic chemical coloring."
        }

    def analyze_ingredients(self, ingredients: List[str], user_profile: Optional[Dict] = None) -> List[IngredientResult]:
        results = []
        for name in ingredients:
            lower_name = name.lower().strip()
            
            # 1. Check for E-codes directly (e.g. E621)
            ecode_match = next((e for e in self.ecodes if e["name"].lower() in lower_name), None)
            
            # 2. Fuzzy match against E-code full names
            if not ecode_match:
                full_names = [e["full_name"] for e in self.ecodes]
                match = process.extractOne(lower_name, full_names, scorer=fuzz.WRatio)
                if match and match[1] >= 80:
                    ecode_match = next(e for e in self.ecodes if e["full_name"] == match[0])

            # 3. Check for harmful keywords
            keyword_match = next((k for k in self.harmful_keywords if k in lower_name), None)

            # 4. Profile-based Allergy Check
            is_allergen = False
            allergy_reason = ""
            if user_profile and "allergies" in user_profile:
                for allergy in user_profile["allergies"]:
                    if allergy.lower() in lower_name:
                        is_allergen = True
                        allergy_reason = f"Matches your allergy: {allergy}"
                        break

            if is_allergen:
                results.append(IngredientResult(
                    name=name,
                    status="danger",
                    reason=allergy_reason
                ))
            elif ecode_match:
                results.append(IngredientResult(
                    name=name,
                    status=ecode_match["status"],
                    reason=f"{ecode_match['full_name']}: {ecode_match['reason']}"
                ))
            elif keyword_match:
                results.append(IngredientResult(
                    name=name,
                    status="caution",
                    reason=self.harmful_keywords[keyword_match]
                ))
            else:
                results.append(IngredientResult(
                    name=name,
                    status="safe",
                    reason="No major concerns found."
                ))
        
        return results

    def calculate_hs_score(self, ingredients: List[IngredientResult], nova_class: int, user_profile: Optional[Dict] = None) -> Dict:
        # Hₛ = max(0, 100 - allergenHits - novaDeduction - eCodeRisk - conditionFlags)
        
        # 1. Allergens (40pts per hit, max 40)
        allergen_hits = sum(1 for i in ingredients if "Matches your allergy" in i.reason)
        allergen_deduction = min(40, allergen_hits * 40)

        # 2. NOVA deduction (max 20pts)
        nova_deduction = min(20, (nova_class - 1) * 6.67)

        # 3. Ingredient Composition Order & Additives Risk (max 30)
        # FSSAI regulations state ingredients are listed in descending order by weight.
        additive_deduction = 0.0
        for i, item in enumerate(ingredients):
            penalty = 0.0
            if item.status == "danger" and "allergy" not in item.reason:
                penalty += 10.0
            elif item.status == "caution":
                penalty += 5.0
                
            name_lower = item.name.lower()
            if any(x in name_lower for x in ["sugar", "syrup", "palm oil", "fructose"]):
                penalty += 4.0

            if penalty > 0:
                if i == 0:
                    additive_deduction += (penalty * 3.0)
                elif i < 3:
                    additive_deduction += (penalty * 2.0)
                elif i < 6:
                    additive_deduction += penalty
                else:
                    additive_deduction += (penalty * 0.5)

        additive_deduction = min(30.0, additive_deduction)

        # 4. Condition Flags (max 20)
        condition_deduction = 0
        if user_profile and "conditions" in user_profile:
            all_text = " ".join([i.name.lower() for i in ingredients])
            if "Diabetes" in user_profile["conditions"]:
                if any(x in all_text for x in ["sugar", "syrup", "maltodextrin"]):
                    condition_deduction += 15
            if "Hypertension" in user_profile["conditions"]:
                if any(x in all_text for x in ["salt", "sodium"]):
                    condition_deduction += 12
            if "High Cholesterol" in user_profile["conditions"]:
                if any(x in all_text for x in ["palm oil", "saturated fat", "lard"]):
                    condition_deduction += 10
        
        condition_deduction = min(20, condition_deduction)

        final_score = max(0, 100 - allergen_deduction - nova_deduction - additive_deduction - condition_deduction)

        return {
            "final_score": round(final_score),
            "breakdown": {
                "allergenDeduction": round(allergen_deduction, 1),
                "novaDeduction": round(nova_deduction, 1),
                "additiveDeduction": round(additive_deduction, 1),
                "conditionDeduction": round(condition_deduction, 1)
            }
        }
