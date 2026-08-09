import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../features/scanner/models/scan_result_model.dart';

/// Fetches product data from Open Food Facts API for a given barcode.
/// Returns null if the product is not found.
Future<ScanResult?> fetchProductByBarcode(String barcode) async {
  final url = Uri.parse(
    'https://world.openfoodfacts.org/api/v2/product/$barcode'
    '?fields=product_name,product_name_en,brands,ingredients_text,'
    'nova_group,nutriments,ecoscore_grade',
  );

  try {
    final response = await http.get(url, headers: {
      'User-Agent': 'NutriScanAI/1.0 (contact@nutriscan.ai)',
    }).timeout(const Duration(seconds: 12));

    if (response.statusCode != 200) return null;

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    // OFF v2 API: status field can be int 1 or string "1"
    final status = data['status'];
    final found = status == 1 || status == '1' || status.toString() == '1';
    if (!found) return null;

    final product = data['product'] as Map<String, dynamic>? ?? {};
    return _mapToScanResult(barcode, product);
  } catch (e) {
    return null;
  }
}

ScanResult _mapToScanResult(String barcode, Map<String, dynamic> product) {
  // ── Product identity ─────────────────────────────────────────────────────────
  final name = _nonEmpty(product['product_name']) ??
      _nonEmpty(product['product_name_en']) ??
      'Unknown Product';
  final brand = (product['brands'] as String?)?.split(',').first.trim() ??
      'Unknown Brand';

  // ── Ingredients ───────────────────────────────────────────────────────────────
  final rawIngredients = product['ingredients_text'] as String? ?? '';
  final ingredientItems = _parseIngredients(rawIngredients);

  // ── Nutrients ─────────────────────────────────────────────────────────────────
  final rawNutri = product['nutriments'];
  final nutriments = rawNutri is Map<String, dynamic> ? rawNutri : <String, dynamic>{};
  final nutrients = _buildNutrients(nutriments);

  // ── NOVA group ────────────────────────────────────────────────────────────────
  final novaRaw = product['nova_group'];
  final novaInt = novaRaw is int
      ? novaRaw
      : int.tryParse(novaRaw?.toString() ?? '') ?? 4;
  final novaGroup = _novaFromInt(novaInt);

  // ── Health score ──────────────────────────────────────────────────────────────
  final healthScore = _computeScore(nutriments, novaGroup, ingredientItems);

  return ScanResult(
    productName: name,
    brand: brand,
    healthScore: healthScore,
    novaGroup: novaGroup,
    nutrients: nutrients,
    ingredients: ingredientItems,
    alternatives: const [],
  );
}

String? _nonEmpty(dynamic v) {
  if (v == null) return null;
  final s = v.toString().trim();
  return s.isEmpty ? null : s;
}

// ── Ingredient parsing ────────────────────────────────────────────────────────

const _flaggedAdditives = <String, String>{
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
  if (raw.trim().isEmpty) return [];

  final cleaned = raw
      .replaceAll(RegExp(r'<[^>]+>'), '')
      .replaceAll(RegExp(r'\([^)]*%[^)]*\)'), '')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  final parts = cleaned
      .split(',')
      .map((s) => s.trim())
      .where((s) => s.isNotEmpty)
      .toList();

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

/// Safely reads a numeric value from the nutriments map.
/// Tries the plain key first, then the _100g suffixed variant.
double? _getNutrient(Map<String, dynamic> n, String key) {
  // Try all common suffixes and variant keys OFF uses
  final candidates = [
    key,
    '${key}_100g',
    '${key}_serving',
    '${key}_value',
    // Special cases for energy
    if (key == 'energy-kcal') ...['energy-kcal_100g', 'energy-kcal_serving', 'energy_100g', 'calories', 'calories_100g'],
    if (key == 'energy') ...['energy_100g', 'energy_serving'],
  ];

  for (final candidate in candidates) {
    final v = n[candidate];
    if (v == null) continue;
    if (v is num) return v.toDouble();
    final parsed = double.tryParse(v.toString());
    if (parsed != null) return parsed;
  }
  return null;
}

List<NutrientInfo> _buildNutrients(Map<String, dynamic> n) {
  // Calories: try kcal key first, fall back to kJ ÷ 4.184
  final kcal = _getNutrient(n, 'energy-kcal');
  final kj = _getNutrient(n, 'energy');
  final cal = kcal ?? (kj != null ? kj / 4.184 : null);

  final sugar = _getNutrient(n, 'sugars');
  final fat = _getNutrient(n, 'fat');

  // OFF stores sodium in grams/100g → convert to mg
  final sodiumG = _getNutrient(n, 'sodium');
  // Sometimes sodium is already in mg (value > 10 is a clue)
  final sodiumMg = sodiumG != null
      ? (sodiumG > 10 ? sodiumG : sodiumG * 1000)
      : null;

  NutritionLevel calLevel(double? v) {
    if (v == null) return NutritionLevel.unknown;
    if (v <= 200) return NutritionLevel.good;
    if (v <= 400) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel sugarLevel(double? v) {
    if (v == null) return NutritionLevel.unknown;
    if (v <= 5) return NutritionLevel.good;
    if (v <= 12.5) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel fatLevel(double? v) {
    if (v == null) return NutritionLevel.unknown;
    if (v <= 3) return NutritionLevel.good;
    if (v <= 17.5) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

  NutritionLevel sodiumLevel(double? v) {
    if (v == null) return NutritionLevel.unknown;
    if (v <= 120) return NutritionLevel.good;
    if (v <= 600) return NutritionLevel.moderate;
    return NutritionLevel.poor;
  }

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

  switch (nova) {
    case NovaGroup.group1: break;
    case NovaGroup.group2: score -= 5; break;
    case NovaGroup.group3: score -= 15; break;
    case NovaGroup.group4: score -= 30; break;
  }

  final flaggedCount = ingredients.where((i) => i.isFlagged).length;
  score -= (flaggedCount * 8).clamp(0, 25).toDouble();

  final sugar = _getNutrient(nutriments, 'sugars') ?? 0;
  final fat = _getNutrient(nutriments, 'fat') ?? 0;
  final saturated = _getNutrient(nutriments, 'saturated-fat') ?? 0;
  final sodiumG = _getNutrient(nutriments, 'sodium') ?? 0;
  final sodium = sodiumG > 10 ? sodiumG : sodiumG * 1000;

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
