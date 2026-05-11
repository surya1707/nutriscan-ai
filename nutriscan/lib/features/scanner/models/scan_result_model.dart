import 'package:uuid/uuid.dart';

/// NutritionLevel indicates whether a nutrient's value is healthy.
enum NutritionLevel { good, moderate, poor }

/// NOVA group classification (1–4) for food processing level.
enum NovaGroup { group1, group2, group3, group4 }

/// A single nutrient item in the nutrition grid.
class NutrientInfo {
  final String name;
  final String value;
  final String unit;
  final NutritionLevel level;

  const NutrientInfo({
    required this.name,
    required this.value,
    required this.unit,
    required this.level,
  });
}

/// A single ingredient in the ingredient list.
class IngredientItem {
  final String name;
  final bool isFlagged;
  final String? flagReason;

  const IngredientItem({
    required this.name,
    this.isFlagged = false,
    this.flagReason,
  });
}

/// A healthier alternative product card.
class AlternativeProduct {
  final String name;
  final String brand;
  final int score;
  final String emoji;

  const AlternativeProduct({
    required this.name,
    required this.brand,
    required this.score,
    required this.emoji,
  });
}

/// The complete result of scanning a food product.
class ScanResult {
  final String id; // UUID primary key
  final String productName;
  final String brand;
  final int healthScore; // 0–100
  final NovaGroup novaGroup;
  final List<NutrientInfo> nutrients;
  final List<IngredientItem> ingredients;
  final List<AlternativeProduct> alternatives;

  ScanResult({
    String? id,
    required this.productName,
    required this.brand,
    required this.healthScore,
    required this.novaGroup,
    required this.nutrients,
    required this.ingredients,
    required this.alternatives,
  }) : id = id ?? const Uuid().v4();
}

// ---------------------------------------------------------------------------
// Mock data for UI development
// ---------------------------------------------------------------------------

final mockScanResult = ScanResult(
  id: 'mock-001',
  productName: 'Chocolate Cream Cookies',
  brand: 'BrandCo',
  healthScore: 28,
  novaGroup: NovaGroup.group4,
  nutrients: const [
    NutrientInfo(name: 'Calories', value: '480', unit: 'kcal', level: NutritionLevel.poor),
    NutrientInfo(name: 'Sugar', value: '34', unit: 'g', level: NutritionLevel.poor),
    NutrientInfo(name: 'Fat', value: '22', unit: 'g', level: NutritionLevel.moderate),
    NutrientInfo(name: 'Sodium', value: '390', unit: 'mg', level: NutritionLevel.moderate),
  ],
  ingredients: const [
    IngredientItem(name: 'Enriched Flour (Wheat Flour, Niacin, Reduced Iron)'),
    IngredientItem(
      name: 'High-Fructose Corn Syrup',
      isFlagged: true,
      flagReason: 'Linked to metabolic disorders',
    ),
    IngredientItem(name: 'Palm Oil'),
    IngredientItem(
      name: 'Artificial Flavors',
      isFlagged: true,
      flagReason: 'Synthetic additive',
    ),
    IngredientItem(name: 'Cocoa (processed with alkali)'),
    IngredientItem(
      name: 'Sodium Benzoate (Preservative)',
      isFlagged: true,
      flagReason: 'Artificial preservative, avoid in excess',
    ),
    IngredientItem(name: 'Soy Lecithin'),
    IngredientItem(name: 'Vanillin (Artificial Vanilla Flavor)', isFlagged: true, flagReason: 'Synthetic flavoring'),
    IngredientItem(name: 'Salt'),
    IngredientItem(name: 'Baking Soda'),
  ],
  alternatives: const [
    AlternativeProduct(name: 'Oat Digestive', brand: 'NaturaBite', score: 74, emoji: '🌾'),
    AlternativeProduct(name: 'Dark Choco Bar', brand: 'PureEat', score: 68, emoji: '🍫'),
    AlternativeProduct(name: 'Rice Crackers', brand: 'HealthSnack', score: 82, emoji: '🌿'),
    AlternativeProduct(name: 'Seed Mix Bar', brand: 'OrganicPro', score: 89, emoji: '🌱'),
  ],
);
