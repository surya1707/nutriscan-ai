import 'package:flutter_test/flutter_test.dart';
import 'package:nutriscan_ai/core/services/safety_score_service.dart';
import 'package:nutriscan_ai/core/providers/user_profile_provider.dart';
import 'package:nutriscan_ai/features/scanner/models/scan_result_model.dart';

void main() {
  group('SafetyScoreService Tests', () {
    test('Computes score correctly for clean ingredients (No deductions)', () {
      const ingredients = [
        IngredientItem(name: 'Apple', isFlagged: false),
        IngredientItem(name: 'Water', isFlagged: false),
      ];
      final profile = UserProfile();

      final breakdown = SafetyScoreService.computePersonalisedScore(
        ingredients: ingredients,
        nova: NovaGroup.group1,
        profile: profile,
      );

      expect(breakdown.finalScore, 100);
      expect(breakdown.allergenDeduction, 0);
      expect(breakdown.novaDeduction, 0);
      expect(breakdown.additiveDeduction, 0);
    });

    test('Allergen deduction is applied correctly', () {
      const ingredients = [
        IngredientItem(name: 'Peanut Butter', isFlagged: false),
        IngredientItem(name: 'Sugar', isFlagged: true),
      ];
      final profile = UserProfile(allergies: {'Peanut'});

      final breakdown = SafetyScoreService.computePersonalisedScore(
        ingredients: ingredients,
        nova: NovaGroup.group3,
        profile: profile,
      );

      expect(breakdown.allergenDeduction, 40.0);
      expect(breakdown.novaDeduction, closeTo(13.34, 0.01));
      expect(breakdown.additiveDeduction, 18.0); 
      expect(breakdown.finalScore, 29); // 100 - 40 - 13.34 - 18 = 28.66 => 29
    });

    test('Condition deduction for Diabetes', () {
      const ingredients = [
        IngredientItem(name: 'Maltodextrin', isFlagged: false),
      ];
      final profile = UserProfile(conditions: {'Diabetes'});

      final breakdown = SafetyScoreService.computePersonalisedScore(
        ingredients: ingredients,
        nova: NovaGroup.group1,
        profile: profile,
      );

      expect(breakdown.conditionDeduction, 15.0);
    });
    
    test('Personalised ingredients correctly flag allergens', () {
      const ingredients = [
        IngredientItem(name: 'Milk', isFlagged: false),
        IngredientItem(name: 'Water', isFlagged: false),
      ];
      final profile = UserProfile(allergies: {'Milk'});

      final result = SafetyScoreService.getPersonalisedIngredients(
        ingredients: ingredients,
        profile: profile,
      );

      expect(result[0].isFlagged, true);
      expect(result[0].flagReason, contains('Milk'));
      expect(result[1].isFlagged, false);
    });
  });
}
