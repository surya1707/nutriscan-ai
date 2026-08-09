import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:network_image_mock/network_image_mock.dart';
import 'package:nutriscan_ai/features/scanner/screens/results_screen.dart';
import 'package:nutriscan_ai/features/scanner/models/scan_result_model.dart';
import 'package:nutriscan_ai/core/services/safety_score_service.dart';

void main() {
  testWidgets('ResultsScreen renders with a mocked ScanResultModel', (WidgetTester tester) async {
    final mockResult = ScanResult(
      productName: 'Mock Product',
      brand: 'Mock Brand',
      healthScore: 85,
      novaGroup: NovaGroup.group1,
      nutrients: [
        NutrientInfo(name: 'Calories', value: '150', unit: 'kcal', level: NutritionLevel.good),
      ],
      ingredients: [
        IngredientItem(name: 'Oats', isFlagged: false),
      ],
      alternatives: [],
      breakdown: SafetyScoreBreakdown(
        allergenDeduction: 0,
        novaDeduction: 0,
        additiveDeduction: 0,
        conditionDeduction: 0,
        nutrientDeduction: 0,
        finalScore: 85,
      ),
    );

    await mockNetworkImagesFor(() async {
      await tester.pumpWidget(
        MaterialApp(
          home: ResultsScreen(result: mockResult),
        ),
      );

      await tester.pumpAndSettle();

      // Check for product info
      expect(find.text('Mock Product'), findsOneWidget);

      // Check for Ingredients
      expect(find.text('Oats'), findsOneWidget);
      
      // Check for Nutrients
      expect(find.text('Calories'), findsOneWidget);
    });
  });
}
