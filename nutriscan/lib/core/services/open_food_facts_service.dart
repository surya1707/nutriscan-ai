import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../features/scanner/models/scan_result_model.dart';

/// Fetches product data from Open Food Facts API for a given barcode.
/// Returns null if the product is not found.
Future<ScanResult?> fetchProductByBarcode(String barcode) async {
  final url = Uri.parse(
    'https://world.openfoodfacts.org/api/v0/product/$barcode.json',
  );

  try {
    final response = await http.get(url, headers: {
      'User-Agent': 'NutriScanAI/1.0 (contact@nutriscan.ai)',
    }).timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) return null;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (data['status'] != 1) return null; // product not found

    final product = data['product'] as Map<String, dynamic>;
    return _mapToScanResult(barcode, product);
  } catch (_) {
    return null;
  }
}

ScanResult _mapToScanResult(
    String barcode, Map<String, dynamic> product) {
  // ── Product identity ──────────────────────────────────────────────────
  final name = (product['product_name'] as String?)?.trim() ??
      (product['product_name_en'] as String?)?.trim() ??
      'Unknown Product';
  final brand = (product['brands'] as String?)
          ?.split(',')
          .first
          .trim() ??
      'Unknown Brand';

  // ── Ingredients ───────────────────────────────────────────────────────
  final rawIngredients =
      product['ingredients_text'] as String? ?? '';
  final ingredientItems = _parseIngredients(rawIngredients);

  // ── Nutrients ─────────────────────────────────────────────────────────
  final nutriments =
      (product['nutriments'] as Map<String, dynamic>?) ?? {};

  final nutrients = _buildNutrients(nutriments);

  // ── NOVA group ────────────────────────────────────────────────────────
  final novaInt = product['nova_group'] as int? ??
      int.tryParse(product['nova_group']?.toString() ?? '') ??
      4;
  final novaGroup = _novaFromInt(novaInt);

  // ── Health score ──────────────────────────────────────────────────────
  final healthScore = _computeScore(nutriments, novaGroup, ingredientItems);

  // ── Alternatives placeholder ──────────────────────────────────────────
  // Will be powered by a recommendation engine later; use empty list for now
  const alternatives = <AlternativeProduct>[];

  return ScanResult(
    productName: name,
    brand: brand,
    healthScore: healthScore,
    novaGroup: novaGroup,
    nutrients: nutrients,
    ingredients: ingredientItems,
    alternatives: alternatives,
  );
}

// ── Ingredient parsing ────────────────────────────────────────────────────────

/// Known industrial additives that should be flagged.
const _flaggedAdditives = {
  'high-fructose corn syrup': 'Linked to metabolic disorders',
  'hfcs': 'High-fructose corn syrup — metabolic risk',
  'partially hydrogenated': 'Contains trans fats — cardiovascular risk',
  'hydrogenated vegetable oil': 'Trans fat source',
  'sodium benzoate': 'Artificial preservative — avoid in excess',
  'potassium bromate': 'Banned in many countries — potential carcinogen',
  'aspartame': 'Artificial sweetener — controversial safety profile',
  'acesulfame': 'Artificial sweetener',
  'saccharin': 'Artificial sweetener',
  'red 40': 'Synthetic dye — linked to hyperactivity',
  'yellow 5': 'Synthetic dye',
  'yellow 6': 'Synthetic dye',
  'blue 1': 'Synthetic dye',
  'carrageenan': 'May cause gut inflammation',
  'monosodium glutamate': 'Flavor enhancer — sensitivity concerns',
  'msg': 'Monosodium glutamate — sensitivity concerns',
  'bha': 'Butylated hydroxyanisole — potential endocrine disruptor',
  'bht': 'Butylated hydroxytoluene — potential endocrine disruptor',
  'sodium nitrate': 'Processed meat preservative — carcinogenic risk',
  'sodium nitrite': 'Processed meat preservative — carcinogenic risk',
  'artificial flavor': 'Synthetic flavoring',
  'artificial flavour': 'Synthetic flavoring',
  'artificial color': 'Synthetic coloring agent',
  'artificial colour': 'Synthetic coloring agent',
  'propyl gallate': 'Synthetic antioxidant — safety concerns',
  'tbhq': 'Tertiary butylhydroquinone — high-dose safety concerns',
};

List<IngredientItem> _parseIngredients(String raw) {
  if (raw.isEmpty) return [];

  // Split on commas, clean up HTML, strip percentages
  final cleaned = raw
      .replaceAll(RegExp(r'<[^>]+>'), '') // strip HTML tags
      .replaceAll(RegExp(r'\([^)]*%[^)]*\)'), '') // remove (XX%) groups
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  final parts = cleaned.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();

  return parts.map((ingredient) {
    final lower = ingredient.toLowerCase();
    String? flagReason;

    for (final entry in _flaggedAdditives.entries) {
      if (lower.contains(entry.key)) {
        flagReason = entry.value;
        break;
      }
    }

    return IngredientItem(
      name: ingredient,
      isFlagged: flagReason != null,
      flagReason: flagReason,
    );
  }).toList();
}

// ── Nutrient building ─────────────────────────────────────────────────────────

List<NutrientInfo> _buildNutrients(Map<String, dynamic> n) {
  double? get(String key) {
    final v = n[key] ?? n['${key}_100g'];
    if (v == null) return null;
    return double.tryParse(v.toString());
  }

  NutritionLevel calLevel(double? v) {
    if (v == null) return NutritionLevel.moderate;
    if (v <= 200) return NutritionLevel.good;
    if (v <= 400) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel sugarLevel(double? v) {
    if (v == null) return NutritionLevel.moderate;
    if (v <= 5) return NutritionLevel.good;
    if (v <= 12.5) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel fatLevel(double? v) {
    if (v == null) return NutritionLevel.moderate;
    if (v <= 3) return NutritionLevel.good;
    if (v <= 17.5) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel sodiumLevel(double? v) {
    if (v == null) return NutritionLevel.moderate;
    if (v <= 120) return NutritionLevel.good;
    if (v <= 600) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  final double? cal = get('energy-kcal') ?? (get('energy') != null ? (get('energy')! / 4.184) : null);
  final sugar = get('sugars');
  final fat = get('fat');
  // sodium in mg (OFF stores as g, multiply by 1000)
  final sodiumG = get('sodium');
  final sodiumMg = sodiumG != null ? sodiumG * 1000 : null;

  return [
    NutrientInfo(
      name: 'Calories',
      value: cal != null ? cal.round().toString() : '—',
      unit: 'kcal',
      level: calLevel(cal),
    ),
    NutrientInfo(
      name: 'Sugar',
      value: sugar != null ? sugar.toStringAsFixed(1) : '—',
      unit: 'g',
      level: sugarLevel(sugar),
    ),
    NutrientInfo(
      name: 'Fat',
      value: fat != null ? fat.toStringAsFixed(1) : '—',
      unit: 'g',
      level: fatLevel(fat),
    ),
    NutrientInfo(
      name: 'Sodium',
      value: sodiumMg != null ? sodiumMg.round().toString() : '—',
      unit: 'mg',
      level: sodiumLevel(sodiumMg),
    ),
  ];
}

// ── Safety score Hₛ ───────────────────────────────────────────────────────────

int _computeScore(
  Map<String, dynamic> nutriments,
  NovaGroup nova,
  List<IngredientItem> ingredients,
) {
  double score = 100;

  // NOVA penalty
  switch (nova) {
    case NovaGroup.group1: break;
    case NovaGroup.group2: score -= 5; break;
    case NovaGroup.group3: score -= 15; break;
    case NovaGroup.group4: score -= 30; break;
  }

  // Flagged additive penalty (up to -25 total)
  final flaggedCount = ingredients.where((i) => i.isFlagged).length;
  score -= (flaggedCount * 8).clamp(0, 25).toDouble();

  // Nutrient score
  double? get(String key) {
    final v = nutriments[key] ?? nutriments['${key}_100g'];
    return v != null ? double.tryParse(v.toString()) : null;
  }

  final sugar = get('sugars') ?? 0;
  final fat = get('fat') ?? 0;
  final saturated = get('saturated-fat') ?? 0;
  final sodiumG = get('sodium') ?? 0;
  final sodium = sodiumG * 1000; // convert to mg

  if (sugar > 22.5) score -= 15;
  else if (sugar > 12.5) score -= 8;

  if (fat > 17.5) score -= 10;
  else if (fat > 3) score -= 4;

  if (saturated > 5) score -= 8;

  if (sodium > 1500) score -= 12;
  else if (sodium > 600) score -= 6;

  return score.round().clamp(0, 100);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

NovaGroup _novaFromInt(int n) {
  switch (n) {
    case 1: return NovaGroup.group1;
    case 2: return NovaGroup.group2;
    case 3: return NovaGroup.group3;
    default: return NovaGroup.group4;
  }
}
