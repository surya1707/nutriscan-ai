import 'dart:math';
import '../providers/user_profile_provider.dart';
import '../../features/scanner/models/scan_result_model.dart';

class SafetyScoreBreakdown {
  final double allergenDeduction;
  final double novaDeduction;
  final double additiveDeduction;
  final double conditionDeduction;
  final double nutrientDeduction;
  final int finalScore;

  const SafetyScoreBreakdown({
    required this.allergenDeduction,
    required this.novaDeduction,
    required this.additiveDeduction,
    required this.conditionDeduction,
    this.nutrientDeduction = 0.0,
    required this.finalScore,
  });
}

class SafetyScoreService {
  /// Computes a personalised safety score (Hₛ) based on product data and user profile.
  static SafetyScoreBreakdown computePersonalisedScore({
    required List<IngredientItem> ingredients,
    required NovaGroup nova,
    required UserProfile profile,
    List<NutrientInfo> nutrients = const [],
  }) {
    // 1. Allergens (40pts per hit, max 40)
    int allergenHitCount = 0;
    for (final ingredient in ingredients) {
      final name = ingredient.name.toLowerCase();
      for (final allergy in profile.allergies) {
        if (name.contains(allergy.toLowerCase())) {
          allergenHitCount++;
        }
      }
    }
    final allergenDeduction = min(40.0, allergenHitCount * 40.0);

    // 2. NOVA deduction (max 20pts)
    // (novaClass - 1) * 6.67
    int novaClass = 1;
    if (nova == NovaGroup.group2) novaClass = 2;
    if (nova == NovaGroup.group3) novaClass = 3;
    if (nova == NovaGroup.group4) novaClass = 4;
    final novaDeduction = min(20.0, (novaClass - 1) * 6.67);

    // 3. Ingredient Composition Order & Additives Risk (max 30)
    // Under FSSAI regulations, ingredients must be listed in descending order of weight/volume.
    double additiveDeduction = 0.0;
    for (int i = 0; i < ingredients.length; i++) {
      final item = ingredients[i];
      final nameLower = item.name.toLowerCase();
      
      double penalty = 0.0;
      if (item.isFlagged) {
         penalty += 5.0;
      }
      
      // Heavy penalties for sugar, syrup, or unhealthy oils at the very top of the list
      if (nameLower.contains('sugar') || nameLower.contains('syrup') || nameLower.contains('palm oil') || nameLower.contains('fructose')) {
         penalty += 4.0; 
      }

      if (penalty > 0) {
        // Multiplier based on FSSAI descending order
        if (i == 0) {
          additiveDeduction += (penalty * 3.0); // 1st ingredient is the primary component
        } else if (i < 3) {
          additiveDeduction += (penalty * 2.0); // Top 3 are major components
        } else if (i < 6) {
          additiveDeduction += penalty;         // Middle of the list
        } else {
          additiveDeduction += (penalty * 0.5); // Trace amounts at the end
        }
      }
    }
    additiveDeduction = min(30.0, additiveDeduction);

    // 4. Conditions (max 20)
    double conditionDeduction = 0;
    final ingredientText = ingredients.map((i) => i.name.toLowerCase()).join(' ');

    if (profile.conditions.contains('Diabetes')) {
      if (ingredientText.contains('sugar') || ingredientText.contains('syrup') || ingredientText.contains('maltodextrin')) {
        conditionDeduction += 15;
      }
    }
    if (profile.conditions.contains('Hypertension')) {
      if (ingredientText.contains('salt') || ingredientText.contains('sodium')) {
        conditionDeduction += 12;
      }
    }
    if (profile.conditions.contains('High Cholesterol')) {
      if (ingredientText.contains('palm oil') || ingredientText.contains('saturated fat') || ingredientText.contains('lard')) {
        conditionDeduction += 10;
      }
    }
    
    conditionDeduction = min(25.0, conditionDeduction);

    // 5. Nutrient Macros Deduction (max 30)
    double nutrientDeduction = 0;
    for (final nut in nutrients) {
      if (nut.level == NutritionLevel.poor) {
        if (nut.name.toLowerCase().contains('sugar')) {
          nutrientDeduction += 15;
        } else {
          nutrientDeduction += 8;
        }
      }
    }
    nutrientDeduction = min(30.0, nutrientDeduction);

    final finalScore = max(0.0, 100.0 - allergenDeduction - novaDeduction - additiveDeduction - conditionDeduction - nutrientDeduction).round();

    return SafetyScoreBreakdown(
      allergenDeduction: allergenDeduction,
      novaDeduction: novaDeduction,
      additiveDeduction: additiveDeduction,
      conditionDeduction: conditionDeduction,
      nutrientDeduction: nutrientDeduction,
      finalScore: finalScore,
    );
  }

  /// Returns a list of ingredients updated with personalised allergy flags.
  static List<IngredientItem> getPersonalisedIngredients({
    required List<IngredientItem> ingredients,
    required UserProfile profile,
  }) {
    return ingredients.map((ingredient) {
      final name = ingredient.name.toLowerCase();
      String? allergyFound;

      for (final allergy in profile.allergies) {
        if (name.contains(allergy.toLowerCase())) {
          allergyFound = allergy;
          break;
        }
      }

      if (allergyFound != null) {
        return IngredientItem(
          name: ingredient.name,
          isFlagged: true,
          flagReason: 'Matches your allergy: $allergyFound',
        );
      }
      return ingredient;
    }).toList();
  }
}
